import csv

import reversion
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from core.mailer import BrevoMailer
from erp.imports.mapper.base import BaseMapper
from erp.imports.mapper.typeform import TypeFormBase, TypeFormMairie
from erp.imports.serializers import ErpImportSerializer
from erp.management.utils import print_error, print_success
from erp.models import Erp

mapper_choices = {
    "base": BaseMapper,
    "typeform_mairie": TypeFormMairie,
    "typeform_base": TypeFormBase,
}


class Command(BaseCommand):
    help = "Valide et importe les données dans le bdd acceslibre. (CSV, séparateur virgule)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Chemin du fichier à traiter",
        )

        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Afficher les erreurs",
        )

        parser.add_argument(
            "--skip_import",
            action="store_true",
            help="Ignore l'étape d'import du fichier. (Seule la validation est opérée.)",
        )

        parser.add_argument(
            "--generate_errors_file",
            action="store_true",
            help="Écrit un CSV d'erreurs rencontrées lors de la validation du fichier",
        )

        parser.add_argument(
            "--mapper",
            type=str,
            default="base",
            help="Mapper à utiliser. Au choix : base (par défaut), typeform_mairie, typeform_base",
        )

        parser.add_argument(
            "--activite",
            type=str,
            default=None,
            help="Activité à spécifier si l'on est sur le mapper typeform_base",
        )

        parser.add_argument(
            "--force_update",
            action="store_true",
            help="Forcer la mise à jour des ERPs dupliqués avec les données de l'import",
        )

        parser.add_argument(
            "--send_emails",
            action="store_true",
            default=False,
            help="Whether we have to send an email to the mail address attached to the newly importer erp (import_email)",
        )

    def handle(self, *args, **options):  # noqa
        self.input_file = options.get("file")
        self.verbose = options.get("verbose", False)
        self.skip_import = options.get("skip_import", False)
        self.generate_errors_file = options.get("generate_errors_file", False)
        self.mapper = options.get("mapper")
        self.activite = options.get("activite", None)
        self.force_update = options.get("force_update", False)
        self.send_emails = options.get("send_emails", False)

        print("Démarrage du script")
        print_success(
            f"""
Paramètres de lancement du script :

    File : {self.input_file}
    Mapper : {self.mapper}
    Activité : {self.activite}
    Verbose : {self.verbose}
    Skip import : {self.skip_import}
    Generate Errors file : {self.generate_errors_file}
    Force update duplicate erp : {self.force_update}
    Send emails to contributor : {self.send_emails}

        """
        )
        if not self.input_file:
            raise CommandError("Précisez un nom de fichier.")
        else:
            print(f"\tTraitement du fichier {self.input_file}")
            try:
                with open(self.input_file, "r") as file:
                    reader = csv.DictReader(file, delimiter=",")
                    lines = list(reader)
                    total_line = len(lines)

                    print_success(f"\t * Validation du fichier {self.input_file} ({total_line} ligne(s) détectée(s))")
                    self.results = {
                        "duplicated": {"count": 0, "msgs": []},
                        "in_error": {"count": 0, "msgs": []},
                        "validated": {"count": 0},
                        "imported": {"count": 0},
                    }
                    for _, row in enumerate(lines, 1):
                        print_success(f"\t     -> Validation ligne {_}/{total_line} ...")
                        erp_duplicated = None
                        while True:
                            try:
                                validated_erp_data = self.validate_data(row, duplicated_erp=erp_duplicated)
                            except Exception as e:
                                if (
                                    isinstance(e, ValidationError)
                                    and "non_field_errors" in e.get_codes()
                                    and "duplicate" in e.get_codes()["non_field_errors"]
                                ):
                                    if not self.force_update:
                                        print_error(
                                            f"Un doublon a été détecté lors du traitement de la ligne {_}: {e}."
                                        )
                                    self.results["duplicated"]["count"] += 1
                                    self.results["duplicated"]["msgs"].append(
                                        {"line": _, "name": row.get("name"), "error": e, "data": row}
                                    )
                                    if self.force_update is True:
                                        existing_erp_pk = int(e.detail["non_field_errors"][1])
                                        erp_duplicated = Erp.objects.get(pk=existing_erp_pk)
                                        continue
                                else:
                                    print_error(
                                        f"Une erreur est survenue lors du traitement de la ligne {_}: {e}. Passage à la ligne suivante."
                                    )
                                    self.results["in_error"]["count"] += 1
                                    self.results["in_error"]["msgs"].append(
                                        {"line": _, "name": row.get("name"), "error": e, "data": row}
                                    )
                            else:
                                print_success("\t         - La ligne est valide et peut-être importée")
                                self.results["validated"]["count"] += 1

                                if not self.skip_import:
                                    print_success("\t * Importation de l'ERP")
                                    try:
                                        with reversion.create_revision():
                                            new_erp = validated_erp_data.save()
                                            reversion.set_comment("Created via import")

                                        if self.send_emails and new_erp.import_email:
                                            BrevoMailer().send_email(
                                                to_list=new_erp.import_email,
                                                template="erp_imported",
                                                context={"erp_url": new_erp.get_absolute_uri()},
                                            )
                                            print_success("\t   ** Mail envoyé")
                                    except Exception as e:
                                        print_error(
                                            f"Une erreur est survenue lors de l'import de la ligne {_}: {e}. Passage à la ligne suivante."
                                        )
                                    else:
                                        self.results["imported"]["count"] += 1
                            break
            except FileNotFoundError:
                raise Exception(f"Le fichier {self.input_file} est introuvable.")
            except Exception as e:
                raise Exception(f"Une erreur est survenue lors du traitement du fichier {self.input_file}: {e}")

            print(self.build_summary())
            if self.generate_errors_file and (
                self.results["in_error"]["count"] or (self.results["duplicated"]["count"]) and not self.force_update
            ):
                error_file = self.write_error_file()
                print_success(f"Le fichier d'erreurs '{error_file}' est disponible.")

    def validate_data(self, row, duplicated_erp=None):
        mapper = mapper_choices.get(self.mapper)
        data = mapper().csv_to_erp(record=row, activite=self.activite)
        serializer = ErpImportSerializer(instance=duplicated_erp, data=data)
        serializer.is_valid(raise_exception=True)
        return serializer

    @staticmethod
    def _get_error_filename():
        return f"errors_{now().strftime('%Y-%m-%d_%Hh%Mm%S')}.csv"

    def write_error_file(self):
        self.error_file_path = self._get_error_filename()
        with open(self.error_file_path, "w") as self.error_file:
            fieldnames = ("line", "name", "error", "data")

            writer = csv.DictWriter(self.error_file, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            if self.results["duplicated"]["count"] and not self.force_update:
                for line in self.results["duplicated"]["msgs"]:
                    writer.writerow(line)
            for line in self.results["in_error"]["msgs"]:
                writer.writerow(line)
        return self.error_file_path

    def build_summary(
        self,
    ):
        return f"""Statistiques sur le fichier {self.input_file}:

    - Validés: {self.results['validated']['count']}
    - Importés: {self.results['imported']['count']}
    - Dupliqués: {self.results['duplicated']['count']}
    - Erreurs: {self.results['in_error']['count']}"""
