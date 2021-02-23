import json
import sys

from datetime import datetime

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from erp.models import Accessibilite, Activite, Commune, Erp
from erp.provider import arrondissements

# Basic/generic fields mapping
FIELDS_MAP = {
    "c_nom": "nom",
    "c_adr_num": "numero",
    "c_adr_voie": "voie",
    "c_com_nom": "commune",
    "c_com_cp": "code_postal",
    "c_com_insee": "code_insee",
    "c_rdv_tel": "telephone",
}

RESERVE_PS = [
    "R\u00e9serv\u00e9 aux professionnels de sant\u00e9",
    "Uniquement pour les professionnels de sant\u00e9",
    "Ouvert uniquement aux professionnels",
]


def fatal(msg):
    print(msg)
    sys.exit(1)


def discard_erp(erp, msg):
    if erp.id is not None:  # exists in db
        erp.published = False
        erp.save()
        msg = "UNPUBLISHED: " + msg
    else:
        msg = "SKIPPED: " + msg
    raise RuntimeError(msg)


class Command(BaseCommand):
    "Imports vaccination centers from open data: https://www.data.gouv.fr/fr/datasets/lieux-de-vaccination-contre-la-covid-19/"

    help = "Importe les établissements centres de vaccination COVID"

    activite = Activite.objects.filter(slug="centre-de-vaccination").first()

    def retrieve_commune_ext(self, erp):
        if erp.code_insee:
            commune_ext = Commune.objects.filter(code_insee=erp.code_insee).first()
            if not commune_ext:
                arrdt = arrondissements.get_by_code_insee(erp.code_insee)
                if arrdt:
                    commune_ext = Commune.objects.filter(
                        nom__iexact=arrdt["commune"]
                    ).first()
        elif erp.code_postal:
            commune_ext = Commune.objects.filter(
                code_postaux__contains=[erp.code_postal]
            ).first()
        else:
            raise RuntimeError(
                f"Champ code_insee et code_postal nuls (commune: {erp.commune})"
            )

        if not commune_ext:
            raise RuntimeError("Impossible de résoudre la commune")

        return commune_ext

    def build_metadata(self, props):
        return {
            "ban_addresse_id": props.get("c_id_adr"),
            "centre_vaccination": {
                "datemaj": props.get("c__edit_datemaj"),
                "structure": {
                    "nom": props.get("c_structure_rais"),
                    "numero": props.get("c_structure_num"),
                    "voie": props.get("c_structure_voie"),
                    "code_postal": props.get("c_structure_cp"),
                    "code_insee": props.get("c_structure_insee"),
                    "commune": props.get("c_structure_com"),
                },
                "date_fermeture": props.get("c_date_fermeture"),
                "date_ouverture": props.get("c_date_ouverture"),
                "url_rdv": props.get("c_rdv_site_web"),
                "modalites": props.get("c_rdv_modalites"),
                "horaires_rdv": {
                    "lundi": props.get("c_rdv_lundi") or "N/C",
                    "mardi": props.get("c_rdv_mardi") or "N/C",
                    "mercredi": props.get("c_rdv_mercredi") or "N/C",
                    "jeudi": props.get("c_rdv_jeudi") or "N/C",
                    "vendredi": props.get("c_rdv_vendredi") or "N/C",
                    "samedi": props.get("c_rdv_samedi") or "N/C",
                    "dimanche": props.get("c_rdv_dimanche") or "N/C",
                },
            },
        }

    def build_commentaire(self, existing):
        date = datetime.today().strftime("%d/%m/%Y")
        return (
            f"Ces informations ont été {'mises à jour' if existing else 'importées'} depuis data.gouv.fr le {date} "
            "https://www.data.gouv.fr/fr/datasets/lieux-de-vaccination-contre-la-covid-19/"
        )

    def check_closed(self, props):
        # Exclusion des centres déjà fermés
        raw_date_fermeture = props.get("c_date_fermeture")
        if raw_date_fermeture:
            date_fermeture = datetime.strptime(raw_date_fermeture, "%Y-%m-%d")
            if date_fermeture < datetime.today():
                return date_fermeture

    def check_reserve_ps(self, props):
        # Exclusion des centres uniquement réservés aux personnels soignants
        modalites = props.get("c_rdv_modalites")
        if modalites and any(test.lower() in modalites.lower() for test in RESERVE_PS):
            return modalites

    def check_equipe_mobile(self, props):
        # Exclusion des équipes mobiles
        modalites = props.get("c_rdv_modalites")
        if modalites:
            if "equipe mobile" in modalites.lower():
                return modalites

    def import_centre(self, source_id, props, geometry):
        # Check if we already have this ERP from a previous import
        erp = Erp.objects.find_by_source_id(Erp.SOURCE_VACCINATION, source_id)
        if not erp:
            erp = Erp(
                source=Erp.SOURCE_VACCINATION,
                source_id=source_id,
                activite=self.activite,
            )
            accessibilite = Accessibilite(erp=erp)
        else:
            accessibilite = erp.accessibilite

        # Vérifications d'exclusion d'import ou de mise à jour
        ferme_depuis = self.check_closed(props)
        if ferme_depuis:
            discard_erp(erp, f"Centre fermé le {ferme_depuis}")

        reserve_ps = self.check_reserve_ps(props)
        if reserve_ps:
            discard_erp(erp, f"Réservé aux professionnels de santé: {reserve_ps}")

        equipe_mobile = self.check_equipe_mobile(props)
        if equipe_mobile:
            discard_erp(erp, f"Équipe mobile écartée: {equipe_mobile}")

        # Basic administrative fields
        for (json_field, model_field) in FIELDS_MAP.items():
            setattr(erp, model_field, props[json_field])

        # Coordinates
        (lon, lat) = geometry["coordinates"][0]
        erp.geom = Point(lon, lat)

        # Commune checks and normalization
        erp.commune_ext = self.retrieve_commune_ext(erp)

        # Strange/invalid phone numbers
        if erp.telephone and len(erp.telephone) > 20:
            erp.telephone = None

        updated = "UPDATE " if erp.id is not None else ""
        print(f"- {updated}{erp.nom}\n  {erp.code_postal} {erp.commune_ext.nom}")

        erp.metadata = self.build_metadata(props)
        erp.save()

        # Basic accessibilite information (informative comment)
        accessibilite.commentaire = self.build_commentaire(erp.id is not None)
        accessibilite.save()

        return erp

    def handle(self, *args, **options):
        self.stdout.write("Importation des centres de vaccination")

        if not self.activite:
            fatal("L'activité Centre de vaccination n'existe pas.")

        errors = []

        with open("data/centres-vaccination.json", "r") as json_file:
            json_data = json.load(json_file)
            if "features" not in json_data:
                fatal("Liste des centres manquante")
            for centre in json_data["features"]:
                try:
                    geometry = centre["geometry"]
                    props = centre["properties"]
                    source_id = props["c_gid"]
                except KeyError as err:
                    errors.append(f"Propriété essentielle manquante: {err}: {centre}")
                try:
                    self.import_centre(source_id, props, geometry)
                except RuntimeError as err:
                    errors.append(f"#{source_id}: {err}")

        if len(errors) > 0:
            print("Erreurs rencontrées :")
            for error in errors:
                print(f"- {error}")
        else:
            print("Aucune erreur rencontrée.")

        print("Importation effectuée.")
