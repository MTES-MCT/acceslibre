import csv

import reversion
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

from erp.imports.serializers import ErpImportSerializer
from erp.models import Erp


class Command(BaseCommand):
    help = "Import cinema aveugles accessibility"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, default="cinemas_audiodescription.csv")

    def handle(self, *args, **kwargs):
        file_path = kwargs["file"]
        with open(file_path, "r") as file:
            reader = csv.DictReader(file, delimiter=";")

            for row in reader:
                if not row["erp_id"]:
                    continue

                erp = Erp.objects.get(pk=row["erp_id"])
                accessibilite = erp.accessibilite.__dict__
                accessibilite["erp_id"] = row["erp_id"]

                if (
                    row["accueil_audiodescription"]
                    == "avec équipement permanent, casques et boîtiers disponibles à l’accueil"
                ):
                    accessibilite["accueil_audiodescription"] = ["avec_équipement_permanent"]

                if (
                    row["accueil_audiodescription"]
                    == "avec équipement permanent nécessitant le téléchargement d'une application sur smartphone"
                ):
                    accessibilite["accueil_audiodescription"] = ["avec_app"]

                if row["accueil_audiodescription"] == "avec équipement occasionnel selon la programmation":
                    accessibilite["accueil_audiodescription"] = ["avec_équipement_occasionnel"]

                if row["accueil_personnels"]:
                    accessibilite["accueil_personnels"] = row["accueil_personnels"]

                if row["entree_balise_sonore"] == "True":
                    accessibilite["entree_balise_sonore"] = True
                elif row["entree_balise_sonore"] == "False":
                    accessibilite["entree_balise_sonore"] = False

                if row["accueil_audiodescription_presence"] == "True":
                    accessibilite["accueil_audiodescription_presence"] = True
                elif row["accueil_audiodescription_presence"] == "False":
                    accessibilite["accueil_audiodescription_presence"] = False

                if row["commentaire"]:
                    accessibilite["commentaire"] = row["commentaire"]

                if not accessibilite["accueil_audiodescription_presence"]:
                    accessibilite["accueil_audiodescription"] = []

                self._update_erp(
                    data={"accessibilite": accessibilite, "activite": erp.activite.nom, **erp.__dict__}, erp=erp
                )

    def _update_erp(self, data, erp=None):
        serializer = ErpImportSerializer(instance=erp, data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            if (
                isinstance(e, ValidationError)
                and "non_field_errors" in e.get_codes()
                and "duplicate" in e.get_codes()["non_field_errors"]
            ):
                existing_erp_pk = int(e.detail["non_field_errors"][1])
                existing_erp = Erp.objects.get(pk=existing_erp_pk)

                return self._update_erp(data=data, erp=existing_erp)
            return
        try:
            with reversion.create_revision():
                erp = serializer.save()
                reversion.set_comment("Created via cinema blindness accessibility import")
        except reversion.errors.RevertError:
            erp = serializer.save()
        except IntegrityError as integrity_error:
            raise integrity_error

        print(f"ERP {erp.id} updated available at: {erp.get_absolute_uri()}")
