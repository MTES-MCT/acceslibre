import csv

from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import ValidationError

from erp.imports.mapper.base import BaseMapper
from erp.imports.mapper.typeform import TypeFormMairie
from erp.imports.serializers import ErpImportSerializer
from erp.management.utils import print_error, print_success

mapper_choices = {"base": BaseMapper, "typeform_mairie": TypeFormMairie}


class Command(BaseCommand):
    help = "Valide et importe les données dans le bdd acceslibre."

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
            "--one_line",
            action="store_true",
            help="Traite seulement une seule ligne de données. Permet de vérifier à priori la cohérence du fichier.",
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
            help="Mapper à utiliser. Au choix : base (par défaut), typeform_mairie",
        )

    def handle(self, *args, **options):  # noqa
        self.input_file = options.get("file")
        self.verbose = options.get("verbose", False)
        self.one_line = options.get("one_line", False)
        self.skip_import = options.get("skip_import", False)
        self.generate_errors_file = options.get("generate_errors_file", False)
        self.mapper = options.get("mapper")

        print("Démarrage du script")
        print_success(
            f"""
Paramètres de lancement du script :

    File : {self.input_file}
    Mapper : {self.mapper}
    Verbose : {self.verbose}
    One Line : {self.one_line}
    Skip import : {self.skip_import}
    Generate Errors file : {self.generate_errors_file}
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
                        "validated": {"count": 0, "erps": []},
                        "imported": {"count": 0, "erps": []},
                    }
                    for _, row in enumerate(lines, 1):
                        print_success(f"\t     -> Validation ligne {_}/{total_line} ...")
                        try:
                            validated_erp_data = self.validate_data(row)
                        except Exception as e:
                            if (
                                isinstance(e, ValidationError)
                                and "non_field_errors" in e.get_codes()
                                and "duplicate" in e.get_codes()["non_field_errors"]
                            ):
                                print_error(
                                    f"Un doublon a été détecté lors du traitement de la ligne {_}: {e}. Passage à la ligne suivante."
                                )
                                self.results["duplicated"]["count"] += 1
                                self.results["duplicated"]["msgs"].append({"line": _, "error": e, "data": row})
                            else:
                                print_error(
                                    f"Une erreur est survenue lors du traitement de la ligne {_}: {e}. Passage à la ligne suivante."
                                )
                                self.results["in_error"]["count"] += 1
                                self.results["in_error"]["msgs"].append({"line": _, "error": e, "data": row})
                        else:
                            print_success("\t         - La ligne est valide et peut-être importée")
                            self.results["validated"]["count"] += 1
                            self.results["validated"]["erps"].append(validated_erp_data)

                            if not self.skip_import:
                                print_success("\t * Importation de l'ERP")
                                try:
                                    erp = validated_erp_data.save()
                                except Exception as e:
                                    print_error(
                                        f"Une erreur est survenue lors de l'import de la ligne {_}: {e}. Passage à la ligne suivante."
                                    )
                                else:
                                    self.results["imported"]["count"] += 1
                                    self.results["imported"]["erps"].append(erp)
                        if self.one_line:
                            break
            except FileNotFoundError:
                raise Exception(f"Le fichier {self.input_file} est introuvable.")
            except Exception as e:
                raise Exception(f"Une erreur est survenue lors du traitement du fichier {self.input_file}: {e}")

            print(self.build_summary())
            if self.generate_errors_file and (self.results["in_error"]["count"] or self.results["duplicated"]["count"]):
                self.write_error_file()
                print_success("Le fichier d'erreurs 'errors.csv' est disponible.")

    def validate_data(self, row):
        mapper = mapper_choices.get(self.mapper)
        data = mapper().csv_to_erp(record=row)
        serializer = ErpImportSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer

    def write_error_file(self):
        with open("errors.csv", "w") as self.error_file:
            fieldnames = (
                "line",
                "error",
                "data",
            )

            writer = csv.DictWriter(self.error_file, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            for line in self.results["duplicated"]["msgs"]:
                writer.writerow(line)
            for line in self.results["in_error"]["msgs"]:
                writer.writerow(line)

    def build_summary(
        self,
    ):
        return f"""Statistiques sur le fichier {self.input_file}:

    - Validés: {self.results['validated']['count']}
    - Importés: {self.results['imported']['count']}
    - Dupliqués: {self.results['duplicated']['count']}
    - Erreurs: {self.results['in_error']['count']}"""
