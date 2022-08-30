import csv
import os
import sys

from django.core.management.base import BaseCommand

from erp.models import Activite, Erp, Commune, Accessibilite
from erp.provider.geocoder import geocode


def clean(string):
    return (
        str(string)
        .replace("\n", " ")
        .replace("«", "")
        .replace("»", "")
        .replace("’", "'")
        .replace('"', "")
        .strip()
    )


def clean_commune(string):
    return clean("".join(i for i in string if not i.isdigit()))


class Command(BaseCommand):
    help = "Importe des données génériques"
    doublons = []

    def handle_5digits_code(self, cpost):
        cpost = clean(cpost).strip()
        if len(cpost) == 4:
            return "0" + cpost
        return cpost

    def import_row(self, row, writer, **kwargs):
        fields = {}
        # nom
        fields["nom"] = row["nom"]
        try:
            lieu_dit, adresse = row["adr"].split('", "')
        except Exception:
            adresse = row["adr"]
            lieu_dit = None
        adresse = f"{adresse} {row['cp']} {row['vil'].split('CEDEX')[0]}"

        try:
            geo_info = geocode(adresse, postcode=self.handle_5digits_code(row["cp"]))
        except Exception as e:
            error = f"Erreur géocodage : {e}"
            print(error)
            row["error"] = error
            writer.writerow(row)
            return None, None
        else:
            if not geo_info:
                error = "Adresse introuvable"
                print(error)
                row["error"] = error
                writer.writerow(row)
                return None, None

        code_insee = geo_info.get("code_insee")

        commune_ext = (
            Commune.objects.filter(code_insee=code_insee).first()
            if code_insee
            else None
        )
        try:
            activite = Activite.objects.get(nom=row["act"]).id
        except Activite.DoesNotExist:
            error = "Activité inexistante : %s" % row["act"]
            print(error)
            row["error"] = error
            writer.writerow(row)
            return None, None

        fields["source"] = "acceo"
        fields["published"] = False
        fields["numero"] = geo_info.get("numero")
        fields["voie"] = geo_info.get("voie")
        fields["lieu_dit"] = lieu_dit
        fields["code_postal"] = geo_info.get("code_postal")
        fields["commune"] = geo_info.get("commune")
        fields["geom"] = geo_info.get("geom")
        fields["commune_ext"] = commune_ext
        fields["activite_id"] = activite

        # checks rest
        if any(
            [
                fields["nom"] == "",
                fields["code_postal"] == "",
                fields["commune"] == "",
                fields["voie"] == "" and fields["lieu_dit"] == "",
                fields["geom"] == "",
            ]
        ):
            return None, None

        # check doublons
        qs = Erp.objects.filter(
            numero=fields["numero"],
            voie__iexact=fields["voie"],
            commune__iexact=fields["commune"],
            code_insee=code_insee,
            activite__pk=fields["activite_id"],
        )
        if qs.count() >= 1:
            duplicated_pks = qs.values_list("pk", flat=True)
        else:
            duplicated_pks = []
        erp = Erp(**fields)
        erp.save()

        accessibilite = Accessibilite(erp=erp)
        accessibilite.entree_porte_presence = None
        accessibilite.accueil_equipements_malentendants_presence = row[
            "accueil_equipements_malentendants_presence"
        ]
        accessibilite.accueil_equipements_malentendants = row[
            "accueil_equipements_malentendants"
        ].split(",")

        accessibilite.save()
        return erp, duplicated_pks

    def get_csv_path(self, filename="generic.csv"):
        here = os.path.abspath(
            os.path.join(os.path.abspath(__file__), "..", "..", "..")
        )
        return os.path.join(
            os.path.dirname(here),
            "data",
            filename,
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mode test",
        )

    def handle(self, *args, **options):
        csv_path = self.get_csv_path()
        self.to_import = []
        self.stdout.write(f"Importation des ERP depuis {csv_path}")
        with open(csv_path, "r") as file:
            reader = csv.DictReader(file, delimiter=";")
            try:
                with open(self.get_csv_path("error.csv"), "w") as error_file:
                    fieldnames = [
                        "nom",
                        "adr",
                        "vil",
                        "cp",
                        "lng",
                        "lat",
                        "id",
                        "act",
                        "accueil_equipements_malentendants_presence",
                        "accueil_equipements_malentendants",
                        "error",
                    ]
                    writer = csv.DictWriter(
                        error_file, fieldnames=fieldnames, delimiter=";"
                    )
                    writer.writeheader()
                    for row in reader:
                        erp, duplicated_pks = self.import_row(row, writer)
                        if erp:
                            self.to_import.append(erp)
                        if duplicated_pks:
                            print(f"Add duplicate: {duplicated_pks}")
                            self.doublons.append(
                                (f"{row['cp']} - {row['nom']}", duplicated_pks)
                            )

            except csv.Error as err:
                sys.exit(f"file {csv_path}, line {reader.line_num}: {err}")
        if len(self.to_import) == 0:
            print("Rien à importer.")
        else:
            print(f"{len(self.to_import)} ERP à importer")
        if len(self.doublons) != 0:
            print(f"Doublons détectés ({len(self.doublons)}): {self.doublons}")
