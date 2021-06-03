# Imports vaccination centers from open data: https://www.data.gouv.fr/fr/datasets/lieux-de-vaccination-contre-la-covid-19/
import requests
import logging

from django.conf import settings
from json import JSONDecodeError

from erp.imports.mapper.vaccination import RecordMapper
from erp.models import Activite

from core import mailer

logger = logging.getLogger(__name__)


def outputPrintStrategy(text, end="\n", flush=False):
    print(text, end=end, flush=flush)


def outputVoidStrategy(text, end="\n", flush=False):
    pass


class ImportVaccinationsCenters:
    API_URL = "https://www.data.gouv.fr/api/1/datasets/lieux-de-vaccination-contre-la-covid-19/"
    output = None
    errors = []
    imported = 0
    skipped = 0

    def __init__(self, is_scheduler=False, mail_notification=False) -> None:
        self.mail_notification = mail_notification
        self.is_scheduler = is_scheduler
        self.output = outputVoidStrategy if is_scheduler else outputPrintStrategy

    def job(self, dataset_url=None, verbose=False):
        # reinitialize class instance properties, as it's long-lived
        # accross imports in a scheduler context
        self.imported = 0
        self.skipped = 0
        self.errors = []

        try:
            for erp in self.do_import(dataset_url):
                self.output("." if erp else "S", "", True)
        except RuntimeError as err:
            logger.error(err)

        if self.is_scheduler and self.mail_notification:
            self._send_report()
        else:
            if verbose and len(self.errors) > 0:
                self.output("Erreurs rencontrées :")
                for error in self.errors:
                    self.output(f"- {error}")

            self.output("Opération effectuée:")
            self.output(f"- {self.imported} centres importés")
            self.output(f"- {self.skipped} écartés")

    def do_import(self, dataset_url):
        json_data = self._get_valid_data(dataset_url)

        activite = Activite.objects.filter(slug="centre-de-vaccination").first()
        if not activite:
            raise RuntimeError("L'activité Centre de vaccination n'existe pas.")

        return self._process_data(json_data, activite)

    def _get_valid_data(self, dataset_url):
        if not dataset_url:
            dataset_url = self._retrieve_latest_dataset_url()

        json_data = self._get_json(dataset_url)

        if "features" not in json_data:
            raise RuntimeError("Liste des centres manquante")

        return json_data["features"]

    def _get_json(self, url):
        try:
            return requests.get(url).json()
        except (requests.exceptions.RequestException, JSONDecodeError) as err:
            raise RuntimeError(
                f"Erreur de récupération des données JSON: {url}:\n  {err}"
            )

    def _retrieve_latest_dataset_url(self):
        try:
            json_data = self._get_json(self.API_URL)
            json_resources = [
                resource
                for resource in json_data["resources"]
                if resource["format"] == "json"
            ]
            if len(json_resources) == 0:
                raise RuntimeError("Jeu de données absent.")
            return json_resources[0]["latest"]
        except (KeyError, IndexError, ValueError) as err:
            raise RuntimeError(
                f"Impossible de parser les données depuis {self.API_URL}:\n{err}"
            )

    def _process_data(self, records, activite):
        for record in records:
            mapped = RecordMapper(record)
            try:
                erp = mapped.process(activite)
                self.imported += 1
                yield erp
            except RuntimeError as err:
                self.errors.append(f"{mapped.props.get('c_nom')} : {err.__str__()}")
                self.skipped += 1
                yield None

    def _send_report(self):
        mailer.mail_admins(
            f"[{settings.SITE_NAME}] Rapport d'importation des centres de vaccination",
            "mail/import_notification.txt",
            {
                "errors": self.errors,
                "imported": self.imported,
                "skipped": self.skipped,
                "SITE_NAME": settings.SITE_NAME,
                "SITE_ROOT_URL": settings.SITE_ROOT_URL,
            },
        )
