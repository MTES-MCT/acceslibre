from django.core.management.base import BaseCommand, CommandError

from core import mattermost
from erp.imports import importer


class Command(BaseCommand):
    help = "Importe un jeu de données"

    def add_arguments(self, parser):
        parser.add_argument(
            "dataset",
            type=str,
            help="Identifiant du jeu de données à importer (gendarmerie, vaccination)",
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
        if dataset == "gendarmerie":
            results = importer.import_gendarmeries(verbose=verbose)
        elif dataset == "vaccination":
            results = importer.import_vaccination(verbose=verbose)
        else:
            raise CommandError(f"Identifiant de jeu de données inconnu: {dataset}")

        summary = build_summary(dataset, results)
        detailed_report = build_detailed_report(results)
        if verbose:
            print(detailed_report + "\n\n" + summary)

        mattermost.send(
            summary,
            attachements=[
                {
                    "pretext": "Détail des erreurs",
                    "text": to_text_list(results["errors"])
                    if results["errors"]
                    else "Aucune erreur rencontrée",
                }
            ],
            tags=[__name__],
        )


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

{to_text_list(results["errors"])}"""


def build_summary(dataset, results):
    return f"""Statistiques d'import {dataset}:

- Importés: {len(results['imported'])}
- Écartés: {len(results['skipped'])}
- Dépubliés: {len(results['unpublished'])}
- Erreurs: {len(results['errors'])}"""
