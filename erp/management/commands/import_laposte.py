import csv

import reversion
from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import ValidationError

from erp import schema
from erp.imports.serializers import ErpImportSerializer
from erp.models import Activite, Erp

mapping = {
    "ACH00001": {
        "OUI": {
            "accueil_equipements_malentendants_presence": True,
            "accueil_equipements_malentendants": ["bim"],
        },
        "NON": {
            "accueil_equipements_malentendants_presence": False,
        },
    },
    "ACH00002": {
        "OUI": {
            "conformite": True,
        },
        "NON": {
            "conformite": False,
        },
    },
    "ACH00003": {
        "OUI": {
            "commentaire": "Pick up accessible aux PMR.",
        }
    },
    "ACH00005": {
        "OUI": {
            "commentaire": "GAB avec prise audio pour malvoyant.",
        }
    },
    "ACH00006": {
        "OUI": {
            "commentaire": "Equipement affranchissement avec prise audio.",
        }
    },
    "ACH00008": {
        "OUI": {
            "commentaire": "Bande de guidage intérieure.",
        }
    },
    "ACH00010": {
        "OUI": {
            "entree_balise_sonore": True,
        },
        "NON": {"entree_balise_sonore": False},
    },
    "ACH00012": {
        "OUI": {
            "commentaire": "Guichet avec tablette PMR.",
        }
    },
    "ACH00013": {
        "OUI": {
            "commentaire": "Présence d'un espace confidentiel accessible .",
        },
        "NON": {"commentaire": "Pas d'espace confidentiel accessible."},
    },
}


class Command(BaseCommand):
    help = "Import ERP from Laposte"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Chemin du fichier à traiter",
        )

    def _convert_access(self, line):
        accessibilite = {}

        stairs = None
        if line.get("ACH00004") in ("OUI", "NON"):
            stairs = bool(line["ACH00004"] == "OUI")

        for access_key, access_map in mapping.items():
            if not (value := line.get(access_key)):
                continue

            if value in access_map:
                new_access = access_map[value].copy()
                if "commentaire" in access_map[value] and accessibilite.get("commentaire"):
                    new_access["commentaire"] = f"{accessibilite.get('commentaire')} {access_map[value]['commentaire']}"

                accessibilite |= new_access

        if value := line.get("ACH00011"):
            if value == "NON":
                if stairs is None:
                    accessibilite |= {"accueil_retrecissement": True}
                else:
                    accessibilite |= {"accueil_cheminement_plain_pied": False}
            elif value == "OUI":
                accessibilite |= {"accueil_cheminement_plain_pied": True, "accueil_retrecissement": False}

        if value := line.get("ACH00015"):
            if value == "NON":
                accessibilite |= {"entree_ascenseur": False, "entree_marches_rampe": schema.RAMPE_AUCUNE}

            elif value == "OUI":
                if stairs is None:
                    accessibilite |= {"entree_plain_pied": True, "entree_largeur_mini": 80}
                else:
                    accessibilite |= {"entree_plain_pied": False, "entree_marches_rampe": schema.RAMPE_AMOVIBLE}

        return accessibilite

    def _create_or_update_erp(self, line, existing_erp=None):
        erp = {
            "nom": "La Poste",
            "activite": self.activite.nom,
            "code_postal": line["Code postal"],
            "commune": line["Localité"],
            "voie": line["Numéro et voie"],
            "source": Erp.SOURCE_LAPOSTE,
        }

        print(f"Managing {erp['nom']}({erp['code_postal']})")
        erp["accessibilite"] = self._convert_access(line)
        if not erp["accessibilite"]:
            return

        serializer = ErpImportSerializer(data=erp, instance=existing_erp, context={"enrich_only": True})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            if (
                isinstance(e, ValidationError)
                and "non_field_errors" in e.get_codes()
                and "duplicate" in e.get_codes()["non_field_errors"]
            ):
                erp_duplicated = Erp.objects.get(pk=int(e.detail["non_field_errors"][1]))
                return self._create_or_update_erp(line, existing_erp=erp_duplicated)
            print(f"Error {e}")
            return

        action = "CREATED"
        if existing_erp:
            action = "UPDATED"

        try:
            with reversion.create_revision():
                new_erp = serializer.save()
                reversion.set_comment(f"{action} via laposte import")
        except reversion.errors.RevertError:
            new_erp = serializer.save()

        print(f"{action} ERP available at {new_erp.get_absolute_uri()}")

    def handle(self, *args, **options):
        self.input_file = options.get("file")
        self.activite = Activite.objects.get(nom__iexact="Bureau de Poste")

        if not self.input_file:
            raise CommandError("Please provide a file.")
        else:
            print(f"Start managing {self.input_file}")
            with open(self.input_file, "r") as file:
                reader = csv.DictReader(file, delimiter=",")
                lines = list(reader)

                for line in lines:
                    self._create_or_update_erp(line)
