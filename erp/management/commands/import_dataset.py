from django.core.management.base import BaseCommand, CommandError

from erp.imports import importer


class Command(BaseCommand):
    help = "Importe un jeu de données"

    def add_arguments(self, parser):
        parser.add_argument(
            "dataset",
            type=str,
            help="Identifiant du jeu de données à importer (gendarmerie, service_public, ...)",
        )

        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Afficher les erreurs",
        )

    def handle(self, *args, **options):  # noqa
        self.stdout.write("Démarrage de l'importation")
        dataset = options.get("dataset")
        verbose = options.get("verbose", False)
        if not dataset:
            raise CommandError("Identifiant du jeu de données à importer manquant")
        elif dataset == "nestenn":
            results = importer.import_nestenn(verbose=verbose)
        elif dataset == "generic":
            results = importer.import_generic(
                verbose=verbose,
            )
        elif dataset == "service_public":
            results = importer.import_service_public(verbose=verbose)
        else:
            raise CommandError(f"Identifiant de jeu de données inconnu: {dataset}")

        summary = build_summary(dataset, results)
        detailed_report = build_detailed_report(results)
        if verbose:
            print(detailed_report + "\n\n" + summary)

        print(summary)
        print(to_text_list(results["errors"]) if results["errors"] else "Aucune erreur rencontrée")


def to_text_list(items):
    return "\n".join(f"- {item}" for item in items)


def build_detailed_report(results):
    return f"""Établissements importés ou mis à jour

{to_text_list(results["imported"])}

Établissement écartés

{to_text_list(results["skipped"])}

Établissement dépubliés

{to_text_list(results["unpublished"])}

Erreurs rencontrées

{to_text_list(results["errors"])}

Activités non mappées

{to_text_list(results["activites_not_found"])}"""


def build_summary(dataset, results):
    return f"""Statistiques d'import {dataset}:

- Importés: {len(results["imported"])}
- Écartés: {len(results["skipped"])}
- Dépubliés: {len(results["unpublished"])}
- Erreurs: {len(results["errors"])}
- Activités: {len(results["activites_not_found"])}"""
