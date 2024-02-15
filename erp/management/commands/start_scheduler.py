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
        schedule.every().day.at("03:05").do(call_command, "refresh_stats")
        schedule.every().day.at("03:35").do(call_command, "purge_obsolete_objects_in_base")
        schedule.every().day.at("03:55").do(call_command, "deleterevisions", keep=20, days=30)
        schedule.every().day.at("05:10").do(call_command, "import_dataset", "gendarmerie")
        schedule.every(30).days.at("02:10").do(call_command, "import_dataset", "service_public")
        if not settings.STAGING:
            schedule.every().day.at("00:40").do(call_command, "export_to_datagouv")
            schedule.every(3).hours.do(call_command, "notify_changed_erps", hours=3)
            schedule.every().thursday.at("14:30").do(call_command, "notify_weekly_unpublished_erps")
            schedule.every().day.at("12:30").do(call_command("notify_daily_drafts"))

    def start(self):
        while True:
            try:
                schedule.run_pending()
            except Exception as err:
                logger.exception("Exception in scheduler", err)
            time.sleep(1)
