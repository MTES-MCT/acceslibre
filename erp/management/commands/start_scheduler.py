import schedule
import time

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from erp.jobs import check_closed_erps, purge_accounts
from subscription.jobs import notify_changed_erps


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        schedule.every().day.at("00:00").do(check_closed_erps.job, verbose=True)
        schedule.every().day.at("04:00").do(purge_accounts.job, verbose=True)
        schedule.every().hour.do(call_command, "purge_tokens")
        if settings.DATAGOUV_API_KEY:
            schedule.every().day.at("01:00").do(call_command, "export_to_datagouv")
        schedule.every(notify_changed_erps.HOURS_CHECK).hours.do(
            notify_changed_erps.job, verbose=True
        )
        schedule.every().hour.do(call_command, "import_dataset", "vaccination")
        schedule.every().day.do(call_command, "import_dataset", "gendarmerie")
        print("Scheduler started")
        while True:
            schedule.run_pending()
            time.sleep(1)
