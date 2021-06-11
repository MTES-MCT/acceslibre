import requests
import sys

from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

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
            return fatal("Identifiant du jeu de données à importer manquant")
        if dataset == "gendarmerie":
            results = importer.import_gendarmeries(verbose=verbose)
        elif dataset == "vaccination":
            results = importer.import_vaccination(verbose=verbose)
        else:
            return fatal(f"Identifiant de jeu de données inconnu: {dataset}")

        summary = build_summary(dataset, results)
        detailed_report = build_detailed_report(results)
        if verbose:
            print(detailed_report + "\n\n" + summary)

        ping_mattermost(summary, results["errors"])


def fatal(msg):
    print(msg)
    sys.exit(1)


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
    environment = "RECETTE" if settings.STAGING else "PRODUCTION"
    datestr = datetime.strftime(datetime.now(), "%d/%m/%Y à %H:%M:%S")
    return f"""Statistiques d'import {dataset} effectué le {datestr} en {environment} ({settings.SITE_HOST}):

- Importés: {len(results['imported'])}
- Écartés: {len(results['skipped'])}
- Dépubliés: {len(results['unpublished'])}
- Erreurs: {len(results['errors'])}"""


def ping_mattermost(summary, errors):
    if not settings.MATTERMOST_HOOK:
        return
    requests.post(
        settings.MATTERMOST_HOOK,
        json={
            "text": summary,
            "attachments": [
                {
                    "pretext": "Détail des erreurs",
                    "text": to_text_list(errors)
                    if errors
                    else "Aucune erreur rencontrée",
                }
            ],
        },
    )
