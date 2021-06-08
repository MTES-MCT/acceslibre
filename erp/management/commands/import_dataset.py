import requests
import sys

from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from erp.imports import fetcher
from erp.imports.importer import Importer
from erp.imports.mapper.gendarmerie import GendarmerieMapper
from erp.imports.mapper.vaccination import VaccinationMapper

from erp.models import Activite


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
            results = import_gendarmeries(verbose=verbose)
        elif dataset == "vaccination":
            results = import_vaccination(verbose=verbose)
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


def import_gendarmeries(verbose=False):
    return Importer(
        "061a5736-8fc2-4388-9e55-8cc31be87fa0",
        fetcher.CsvFetcher(delimiter=";"),
        GendarmerieMapper,
        Activite.objects.get(slug="gendarmerie"),
        verbose=verbose,
    ).process()


def import_vaccination(verbose=False):
    return Importer(
        "d0566522-604d-4af6-be44-a26eefa01756",
        fetcher.JsonFetcher(hook=lambda x: x["features"]),
        VaccinationMapper,
        Activite.objects.get(slug="centre-de-vaccination"),
        verbose=verbose,
    ).process()


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
    requests.post(
        "https://mattermost.incubateur.net/hooks/gam18nzoqjga5pjzrq6esg4pfr",
        json={
            "text": summary,
            "attachments": [
                {
                    "pretext": "Détail des erreurs",
                    "text": to_text_list(errors),
                }
            ],
        },
    )
