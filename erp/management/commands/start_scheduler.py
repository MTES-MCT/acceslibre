import logging
import time
from datetime import datetime, timezone

import schedule
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from erp.management.commands.outscraper_acquisition import QUERIES as outscraper_queries
from erp.provider.departements import DEPARTEMENTS

logger = logging.getLogger(__name__)

INTERVAL_BETWEEN_2_ACQUISITIONS = 5  # minutes


class Command(BaseCommand):
    tasks = []

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.register_tasks()
        self.setup()
        self.start()

    def register_tasks(self, *args, **kwargs):
        if settings.DEBUG or settings.STAGING:
            print("No acquisition when DEBUG or STAGING is True")
            return

        # NOTE: ATM there is no way to launch a task at a given day in month, so, build a list of tasks to run, and
        # every min, check if we have a task to launch
        min = hour = day = 1
        for term, activity in outscraper_queries:
            for num, data in DEPARTEMENTS.items():
                if min >= 59:
                    min = 1
                    hour += 1

                if hour >= 24:
                    min = hour = 1
                    day += 1

                if day >= 28:
                    min = hour = day = 1
                min += INTERVAL_BETWEEN_2_ACQUISITIONS

                if any([str(num).startswith(x) for x in ["97", "98"]]):
                    # ignore DOM, no data for them
                    continue

                query = f"{term}, {data['nom']}"
                self.tasks.append(
                    {
                        "day": day,
                        "hour": hour,
                        "min": min,
                        "command": "outscraper_acquisition",
                        "command_args": {"query": query, "activity": activity},
                    }
                )

    def _acquisition(self):
        now = datetime.now(timezone.utc)
        for task in self.tasks:
            if task["day"] == now.day and task["hour"] == now.hour and task["min"] == now.minute:
                call_command(task["command"], **task["command_args"])

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
            schedule.every().day.at("12:30").do(call_command, "notify_daily_draft")

        schedule.every().minutes.do(self._acquisition)

    def start(self):
        while True:
            try:
                schedule.run_pending()
            except Exception as err:
                logger.exception("Exception in scheduler", err)
            time.sleep(1)
