"Imports vaccination centers from open data: https://www.data.gouv.fr/fr/datasets/lieux-de-vaccination-contre-la-covid-19/"

import requests

from django.conf import settings

from core import mailer
from erp.mapper import RecordMapper
from erp.models import Activite


API_URL = "https://www.data.gouv.fr/api/1/datasets/lieux-de-vaccination-contre-la-covid-19/"


def job(dataset_url='', verbose=False, report=False):
    json_data = _get_valid_data(dataset_url)

    activite = Activite.objects.filter(slug="centre-de-vaccination").first()
    if not activite:
        raise RuntimeError("L'activité Centre de vaccination n'existe pas.")

    errors, imported, skipped = _process_data(json_data, activite, verbose)

    if verbose and len(errors) > 0:
        print("Erreurs rencontrées :")
        for error in errors:
            print(f"- {error}")

    print("Opération effectuée:")
    print(f"- {imported} centres importés")
    print(f"- {skipped} écartés")

    if report:
        _send_report(errors, imported, skipped)


def _get_valid_data(dataset_url):
    if not dataset_url:
        dataset_url = _retrieve_latest_dataset_url()

    json_data = _retrieve_json_data(dataset_url)

    if "features" not in json_data:
        raise RuntimeError("Liste des centres manquante")

    return json_data["features"]


def _get_json(url):
    try:
        return requests.get(url).json()
    except requests.exceptions.RequestException as err:
        raise RuntimeError(
            f"Erreur de récupération des données JSON: {url}:\n  {err}"
        )


def _retrieve_latest_dataset_url():
    try:
        json_data = _get_json(API_URL)
        json_resources = [
            resource
            for resource in json_data["resources"]
            if resource["format"] == "json"
        ]
        if len(json_resources) == 0:
            raise RuntimeError("Jeu de donnée JSON abenst.")
        return json_resources[0]["latest"]
    except (KeyError, IndexError, ValueError) as err:
        raise RuntimeError(
            f"Impossible de parser les données depuis {API_URL}:\n{err}"
        )


def _retrieve_json_data(dataset_url):
    return _get_json(dataset_url)


def _process_data(records, activite, verbose=False):
    errors = []
    imported = 0
    skipped = 0

    for record in records:
        try:
            erp = RecordMapper(record).process(activite)
            if verbose:
                print(f"- {erp.nom}\n  {erp.code_postal} {erp.commune_ext.nom}")
            else:
                print(".", end="", flush=True)
            imported += 1
        except RuntimeError as err:
            if not verbose:
                print("S", end="", flush=True)
            errors.append(err)
            skipped += 1


def _send_report(errors, imported, skipped):
    mailer.mail_admins(
        f"[{settings.SITE_NAME}] Rapport d'importation des centres de vaccination",
        "mail/import_vaccination_notification.txt",
        {
            "errors": errors,
            "imported": imported,
            "skipped": skipped,
            "SITE_NAME": settings.SITE_NAME,
            "SITE_ROOT_URL": settings.SITE_ROOT_URL,
        },
    )
