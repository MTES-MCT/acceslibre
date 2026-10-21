"""
Management command to match Éducation nationale (EdNat) schools with Acceslibre ERPs.
"""

import csv
from collections import defaultdict

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.functions import Lower

from erp.imports.mapper.base import BaseMapper
from erp.models import Activite, Erp


ACTIVITIES = [
    "Collège",
    "École élémentaire",
    "École maternelle",
    "École primaire (regroupement maternelle et élémentaire)",
    "Groupe scolaire",
    "Lycée",
]

INITIAL_CSV_FILE_HEADERS = [
    "Numéro d'UAI",
    "Appellation officielle",
    "Dénomination principale",
    "Dénomination complémentaire ou patronyme",
    "Secteur",
    "Adresse : désignation de la voie",
    "Adresse : 5e ligne",
    "Adresse : boite postale ou course spéciale",
    "Adresse : code postal",
    "Localité d'acheminement",
    "Libellé de la commune",
    "Géolocalisation : coordonnée X",
    "Géolocalisation : coordonnée Y",
    "EPSG",
    "Latitude WGS84",
    "Longitude WGS84",
    "Appariement par IGN",
    "localisation par IGN",
    "Code nature de l'UAI",
    "Libellé de la nature de l'UAI",
    "Etat de l'établissement",
    "Libellé de l'état de l'établissement",
    "Code INSEE du département ou de la collectivité",
    "Code INSEE de la région",
    "Code de l'académie",
    "Code INSEE de la commune",
    "Libellé du département ou de la collectivité",
    "Libellé de la région",
    "Libellé de l'académie",
    "Latitude et longitude WGS84",
    "Code du type de contrat",
    "Libellé du type de contrat",
    "Code de la tutelle ministérielle",
    "Libellé de la tutelle",
    "Date de rentrée pédagogique",
    "Sigle de l'UAI",
    "Identifiants RNB",
]


class Command(BaseCommand):
    help = "Match Éducation nationale CSV with Acceslibre ERPs"

    def add_arguments(self, parser):
        parser.add_argument("input_file", type=str, help="Path to ednat.csv")
        parser.add_argument("--output-file", type=str, default="ednat_acceslibre_matching.csv", help="Output CSV file")
        parser.add_argument("--max-radius-km", type=float, default=0.5, help="Max radius for geo matching (km)")

    def search_by_rnb_id(self, rnb_ids=None):
        if not rnb_ids:
            return False
        if not isinstance(rnb_ids, (list, tuple)):
            rnb_ids = [rnb_ids]
        qs = Erp.objects.filter(sources__source="rnb", sources__source_id__in=rnb_ids)
        return qs.all()

    def search_by_name_and_postal_code(self, name, postal_code, activities=None, city=None):
        if not name:
            return False
        postal_code = BaseMapper.handle_5digits_code(postal_code)
        qs = Erp.objects.filter(published=True, code_postal=postal_code)
        if activities:
            qs = qs.filter(activite__in=activities)
        if city:
            city = city.strip()
            qs_city = qs.filter(Q(commune__iexact=city) | Q(commune_ext__code_insee__iexact=city))
            if qs_city.exists():
                qs = qs_city
            else:
                qs = qs.filter(Q(commune__icontains=city))
        qs = qs.search_what(name)
        return qs.all()

    def search_by_activity_and_exact_location(self, lon, lat, activities, max_radius_km):
        if not activities or not lon or not lat:
            return False
        point = Point(float(lon), float(lat), srid=4326)
        qs = Erp.objects.filter(activite__in=activities).nearest(point, max_radius_km=max_radius_km)
        return qs.all()

    def handle(self, *args, **options):
        input_file = options["input_file"]
        output_file = options["output_file"]
        max_radius_km = options["max_radius_km"]

        nbs = defaultdict(int)
        activities = Activite.objects.annotate(nom_lower=Lower("nom")).filter(
            nom_lower__in=[a.lower() for a in ACTIVITIES]
        )

        with (
            open(input_file, "r") as infile,
            open(output_file, "w+") as outfile,
        ):
            reader = csv.DictReader(infile, delimiter=";")
            writer = csv.DictWriter(
                outfile,
                fieldnames=INITIAL_CSV_FILE_HEADERS
                + ["uuid_acceslibre", "nom_acceslibre", "adresse_acceslibre", "methode", "noms_acceslibre_potentiels"],
            )
            writer.writeheader()
            for nb, line in enumerate(reader, start=0):
                self.stdout.write(f"Line {nb}/63986")
                found = self.search_by_name_and_postal_code(
                    line["Appellation officielle"] + " " + line["Dénomination complémentaire ou patronyme"],
                    line["Adresse : code postal"],
                    activities=activities,
                    city=line.get("Libellé de la commune") or line.get("Localité d'acheminement") or "",
                )
                if found:
                    nbs["found"] += 1
                    nbs["found_with_search_by_name_and_postal_code"] += 1
                    values = {k: line[k] for k in INITIAL_CSV_FILE_HEADERS}
                    erp = found.first()
                    values["uuid_acceslibre"] = erp.uuid
                    values["nom_acceslibre"] = erp.nom
                    values["adresse_acceslibre"] = erp.adresse
                    values["methode"] = "name_and_postal_code"
                    writer.writerow(values)
                    continue

                found = self.search_by_rnb_id(line["Identifiants RNB"])
                if found:
                    nbs["found"] += 1
                    nbs["found_with_rnb_id"] += 1
                    values = {k: line[k] for k in INITIAL_CSV_FILE_HEADERS}
                    erp = found.first()
                    values["uuid_acceslibre"] = erp.uuid
                    values["nom_acceslibre"] = erp.nom
                    values["adresse_acceslibre"] = erp.adresse
                    values["methode"] = "rnb_id"
                    writer.writerow(values)
                    continue

                longitude = line["Géolocalisation : coordonnée X"]
                latitude = line["Géolocalisation : coordonnée Y"]

                found = self.search_by_activity_and_exact_location(
                    longitude.replace(",", "."),
                    latitude.replace(",", "."),
                    activities=activities,
                    max_radius_km=max_radius_km,
                )
                if found:
                    nbs["found"] += 1
                    nbs["found_with_search_by_activity_and_exact_location"] += 1
                    values = {k: line[k] for k in INITIAL_CSV_FILE_HEADERS}
                    values["noms_acceslibre_potentiels"] = " / ".join([x.nom for x in found])
                    values["methode"] = "activity_and_exact_location"
                    writer.writerow(values)
                    continue

                self.stdout.write("Not found")

        self.stdout.write("Results")
        self.stdout.write(str(dict(nbs)))
