import logging
import time

import schedule
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.setup()
        self.start()

    def setup(self):
        schedule.every().hour.at(":25").do(call_command, "purge_tokens")
        schedule.every().hour.at(":45").do(call_command, "calculate_challenge_stats")
        schedule.every().day.at("03:05").do(call_command, "refresh_global_stats")
        schedule.every().day.at("03:35").do(call_command, "purge_inactive_accounts")
        # Keep revisions from last 30 days and at least 20 from older changes
        schedule.every().day.at("03:55").do(call_command, "deleterevisions", keep=20, days=30)
        schedule.every().day.at("04:10").do(call_command, "import_dataset", "vaccination")
        schedule.every().day.at("05:10").do(call_command, "import_dataset", "gendarmerie")
        if not settings.STAGING:
            schedule.every().day.at("00:40").do(call_command, "export_to_datagouv")
            schedule.every(3).hours.do(call_command, "notify_changed_erps", hours=3)
            schedule.every().thursday.at("14:30").do(call_command, "notify_unpublished_erps")
            schedule.every().monday.at("14:30").do(call_command, "notify_activity_suggestions")

    def start(self):
        while True:
            try:
                schedule.run_pending()
            except Exception as err:
                logger.exception("Exception in scheduler", err)
            time.sleep(1)
