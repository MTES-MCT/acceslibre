import json
import logging
import urllib.parse

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

from erp.exceptions import PermanentlyClosedException
from erp.imports.serializers import ErpImportSerializer
from erp.models import ACTIVITY_GROUPS, Activite, Erp, ExternalSource

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import ERP accessibility info from ApiDAE."

    auth_params = {
        "projetId": settings.APIDAE_PROJECT_ID,
        "apiKey": settings.APIDAE_API_KEY,
    }

    mapping_activities = {
        "PATRIMOINE_CULTUREL": Activite.objects.get(nom="Lieu de visite"),
        "HOTELLERIE": Activite.objects.get(nom="Hôtel"),
        "RESTAURATION": Activite.objects.get(nom="Restaurant"),
        "COMMERCE_ET_SERVICE": Activite.objects.get(nom="Commerce"),
        "HEBERGEMENT_COLLECTIF": Activite.objects.get(nom="Chambre d'hôtes, gîte, pension, meublé de tourisme"),
        "EQUIPEMENT": None,
        "FETE_ET_MANIFESTATION": None,
    }

    def _get_query_for_params(self, params):
        params = {**self.auth_params, **params}
        json_string = json.dumps(params, separators=(",", ":"))
        encoded_json = urllib.parse.quote(json_string)
        return encoded_json

    def _do_request(self, url):
        try:
            response = requests.get(url, timeout=3)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error requesting API : %s", e)
            return

        try:
            data = response.json()
        except ValueError:
            logger.error("Non JSON response: %s", response.text)
            return
        return data

    @staticmethod
    def _ensure_not_permanently_closed(qs):
        if any([erp.permanently_closed for erp in qs]):
            raise PermanentlyClosedException()

    def _find_erp_by_name_and_code_postal(self, name, postal_code):
        qs = Erp.objects.search_what(name).filter(code_postal=postal_code)
        self._ensure_not_permanently_closed(qs)
        return qs.published().first()

    def _has_access_info(self, access_info):
        for aspect in access_info:
            libelle = aspect.get("libelleFr")
            if libelle in [
                "Accessible en fauteuil roulant en autonomie",
                "Place réservée PMR",
                "Place adaptée PMR",
                "Revêtement dur (goudron, ciment, plancher)",
                "Cheminement de plain-pied",
                "Entrée accessible",
                "Ascenseur aux normes",
                "Douche avec assise + espace de circulation",
                "WC + barre d'appui + espace de circulation",
                "Alarme visuelle avec flash lumineux",
                "Boucle magnétique disponible à l’accueil",
                "Possibilité de communiquer en Langue des Signes Française",
                "Cheminement sans obstacles à l'intérieur",
                "Personnel d’accueil sensibilisé à l’accueil des personnes en situation de handicap",
            ]:
                return True
        return False

    def _get_mapped_access_info(self, access_info, is_large_establishment, is_hosting):
        data = {}
        for aspect in access_info:
            libelle = aspect.get("libelleFr")

            if libelle == "Accessible en fauteuil roulant en autonomie":
                data["entree_largeur_mini"] = 80
                data["commentaire"] = "Accessible en fauteuil roulant en autonomie (source: office du tourisme local)"

            elif libelle == "Place réservée PMR":
                data["stationnement_presence"] = True
                data["stationnement_pmr"] = True

            elif libelle == "Place adaptée PMR":
                data["stationnement_presence"] = True

            elif libelle == "Revêtement dur (goudron, ciment, plancher)":
                data["chemin_ext_presence"] = True
                data["cheminement_ext_terrain_stable"] = True

            elif libelle == "Cheminement de plain-pied":
                data["chemin_ext_presence"] = True
                data["chemin_ext_plain_pied"] = True

            elif libelle == "Entrée accessible":
                data["entree_plain_pied"] = True
                data["entree_largeur_mini"] = 80

            elif libelle == "Ascenseur aux normes" and is_large_establishment:
                data["accueil_ascenseur_etage"] = True
                data["accueil_ascenseur_etage_pmr"] = True

            elif libelle == "Douche avec assise + espace de circulation" and is_hosting:
                data["accueil_chambre_nombre_accessibles"] = 1
                data["accueil_chambre_douche_siege"] = True

            elif libelle == "WC + barre d'appui + espace de circulation" and is_hosting:
                data["accueil_chambre_nombre_accessibles"] = 1
                data["accueil_chambre_sanitaires_barre_appui"] = True
                data["accueil_chambre_sanitaires_espace_usage"] = True

            elif libelle == "Alarme visuelle avec flash lumineux" and is_hosting:
                data["accueil_chambre_equipement_alerte"] = True

            elif libelle == "Boucle magnétique disponible à l’accueil":
                data["accueil_equipements_malentendants_presence"] = True
                data["accueil_equipements_malentendants"] = ["bim"]

            elif libelle == "Possibilité de communiquer en Langue des Signes Française":
                data["accueil_equipements_malentendants_presence"] = True
                data["accueil_equipements_malentendants"] = ["lsf"]

            elif libelle == "Cheminement sans obstacles à l'intérieur":
                data["accueil_retrecissement"] = False

            elif libelle == "Personnel d’accueil sensibilisé à l’accueil des personnes en situation de handicap":
                data["accueil_personnels"] = "formés"

        return data

    def _parse_page(self, page):
        count = 200
        self.stdout.write(f"Parsing page {page}")
        params = self._get_query_for_params({"count": count, "first": page * count})

        url = settings.APIDAE_HOST + f"/api/v002/recherche/list-identifiants?query={params}"

        self.stdout.write(f"API Call: {url}")
        data_list = self._do_request(url)

        if not data_list.get("objetTouristiqueIds"):
            self.stdout.write(f"No touristic object found: {data_list}")
            return

        touristic_object_ids = data_list["objetTouristiqueIds"]

        params = self._get_query_for_params({"selectionIds": touristic_object_ids})

        if touristic_object_ids:
            for touristic_object_id in touristic_object_ids:
                url = (
                    settings.APIDAE_HOST
                    + f"/api/v002/objet-touristique/get-by-id/{touristic_object_id}?projetId={settings.APIDAE_PROJECT_ID}&apiKey={settings.APIDAE_API_KEY}&responseFields=@all"
                )
                data_detail = self._do_request(url)

                if not (access_info := data_detail.get("prestations", {}).get("tourismesAdaptes")):
                    continue

                self.stdout.write(f"Managing {data_detail.get('nom', {}).get('libelleFr')}")
                if not self._has_access_info(access_info):
                    self.stdout.write(f"No mapped access info for touristic object {touristic_object_id}")
                    continue

                try:
                    erp = self._find_erp_by_name_and_code_postal(
                        data_detail["nom"]["libelleFr"], data_detail["localisation"]["adresse"]["codePostal"]
                    )
                except PermanentlyClosedException:
                    self.stderr.write(f"ERP {data_detail['nom']['libelleFr']} is permanently closed")
                    continue

                if erp:
                    erp_data = {}
                    for key in ("nom", "commune", "code_postal", "activite"):
                        erp_data[key] = getattr(erp, key)
                    groups = erp.activite.groups.all() if erp.activite else []
                else:
                    if not self.mapping_activities.get(data_detail["type"]):
                        self.stderr.write(
                            f"Non mapped activity for ERP {data_detail['nom']['libelleFr']} not found, creating"
                        )
                        continue
                    self.stderr.write(f"ERP {data_detail['nom']['libelleFr']} not found, creating")
                    erp_data = {
                        "nom": data_detail["nom"]["libelleFr"],
                        "commune": data_detail["localisation"]["adresse"]["commune"]["nom"],
                        "code_postal": data_detail["localisation"]["adresse"]["codePostal"],
                        "voie": data_detail["localisation"]["adresse"]["adresse1"],
                        "activite": self.mapping_activities.get(data_detail["type"]),
                    }

                    groups = self.mapping_activities.get(data_detail["type"]).groups.all()

                is_large_establishment = ACTIVITY_GROUPS["LARGE_ESTABLISHMENTS"] in [g.name for g in groups]
                is_hosting = ACTIVITY_GROUPS["HOSTING"] in [g.name for g in groups]

                if erp:
                    print("Editing access of ", erp.nom, erp.get_absolute_uri())
                else:
                    print(
                        "Creating ",
                        data_detail["nom"]["libelleFr"],
                        data_detail["localisation"]["adresse"]["codePostal"],
                    )

                data = self._get_mapped_access_info(access_info, is_large_establishment, is_hosting)

                if not data:
                    continue

                erp_data["accessibilite"] = data
                erp_data["sources"] = [{"source": ExternalSource.SOURCE_APIDAE, "source_id": data_detail["id"]}]
                try:
                    enrich_only = False
                    if erp and erp.user:
                        enrich_only = True
                    serializer = ErpImportSerializer(data=erp_data, instance=erp, context={"enrich_only": enrich_only})
                    try:
                        serializer.is_valid(raise_exception=True)
                    except ValidationError as e:
                        if "Adresse non localisable" in e.detail["non_field_errors"][0]:
                            self.stderr.write(
                                f"Adresse non localisable: {erp['adresse']} {erp['code_postal']} {erp['commune']}"
                            )
                            continue
                    erp = serializer.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"Successfully updated access info for {erp.nom}, {erp.get_absolute_uri()}")
                    )
                except IntegrityError as e:
                    self.stderr.write(f"Error updating access info: {e}")

        if data_list["numFound"] >= count:
            self._parse_page(page + 1)

    def handle(self, *args, **options):
        self._parse_page(0)

        self.stdout.write(self.style.SUCCESS("END."))
