import logging
import schedule
import time
import traceback

from django.core.management import call_command, CommandError
from django.core.management.base import BaseCommand

from core import mattermost


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        schedule.every().day.at("04:00").do(call_command, "purge_inactive_accounts")
        schedule.every().hour.do(call_command, "purge_tokens")
        schedule.every().day.at("01:00").do(call_command, "export_to_datagouv")
        schedule.every(3).hours.do(call_command, "notify_changed_erps", hours=3)
        schedule.every().hour.do(call_command, "import_dataset", "vaccination")
        schedule.every().day.do(call_command, "import_dataset", "gendarmerie")
        print("Scheduler started")
        while True:
            try:
                schedule.run_pending()
            except CommandError as err:
                trace = traceback.format_exc()
                logger.error(err)
                mattermost.send(
                    f"Erreur d'exécution de la commande: {err}",
                    attachements=[{"pretext": "Stack trace", "text": trace}],
                    tags=[__name__],
                )
            time.sleep(1)
