import json
import sys

from datetime import datetime

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from erp.models import Accessibilite, Activite, Commune, Erp
from erp.provider import arrondissements

FIELDS_MAP = {
    "c_nom": "nom",
    "c_adr_num": "numero",
    "c_adr_voie": "voie",
    "c_com_nom": "commune",
    "c_com_cp": "code_postal",
    "c_com_insee": "code_insee",
    "c_rdv_tel": "telephone",
    "c__edit_datemaj": "2021/02/03 15:19:36.488",
}


class Command(BaseCommand):
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
                "horaires_rdv": {
                    "lundi": props.get("c_rdv_lundi"),
                    "mardi": props.get("c_rdv_mardi"),
                    "mercredi": props.get("c_rdv_mercredi"),
                    "jeudi": props.get("c_rdv_jeudi"),
                    "vendredi": props.get("c_rdv_vendredi"),
                    "samedi": props.get("c_rdv_samedi"),
                    "dimanche": props.get("c_rdv_dimanche"),
                },
            },
        }

    def build_commentaire(self, metadata):
        date = datetime.today().strftime("%d/%m/%Y")
        return f"Ces informations ont été importées depuis data.gouv.fr le {date}: https://www.data.gouv.fr/fr/datasets/lieux-de-vaccination-contre-la-covid-19/"

    def import_centre(self, centre):
        props = centre["properties"]
        geometry = centre["geometry"]
        source = "centres-vaccination"  # XXX: use model constant
        source_id = props["c_gid"]

        # Check if we already have this ERP
        existing = True
        erp = Erp.objects.find_by_source_id(source, source_id)
        if not erp:
            erp = Erp(
                source=source,
                source_id=source_id,
                activite=self.activite,
            )
            existing = False
            accessibilite = Accessibilite(erp=erp)
        else:
            accessibilite = erp.accessibilite

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

        updated = "UPDATE " if existing else ""
        print(f"- {updated}{erp.nom}\n  {erp.code_postal} {erp.commune_ext.nom}")

        erp.metadata = self.build_metadata(props)
        erp.save()

        # Basic accessibilite information (informative comment)
        accessibilite.commentaire = self.build_commentaire(erp.metadata)
        accessibilite.save()

        return erp

    def handle(self, *args, **options):
        self.stdout.write("Importation des centres de vaccination")

        if not self.activite:
            sys.exit("L'activité Centre de vaccination n'existe pas.")

        errors = []

        with open("data/centres-vaccination.json", "r") as json_file:
            json_data = json.load(json_file)
            if "features" not in json_data:
                sys.exit("Liste des centres manquante")
            for centre in json_data["features"]:
                try:
                    self.import_centre(centre)
                except RuntimeError as err:
                    errors.append(err)
        if len(errors) > 0:
            print("Erreurs rencontrées :")
            for error in errors:
                print(f"- {error}")
        else:
            print("Aucune erreur rencontrée.")
        print("Importation effectuée.")
