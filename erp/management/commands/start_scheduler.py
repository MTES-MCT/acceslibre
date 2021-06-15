import schedule
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

from erp.jobs import purge_accounts
from subscription.jobs import notify_changed_erps


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        # TODO: move purge_accounts job to a compte app command
        schedule.every().day.at("04:00").do(purge_accounts.job, verbose=True)
        schedule.every().hour.do(call_command, "purge_tokens")
        # TODO: move notify_changed_erps job to a subscription app command
        schedule.every(notify_changed_erps.HOURS_CHECK).hours.do(
            notify_changed_erps.job, verbose=True
        )
        schedule.every().hour.do(call_command, "import_dataset", "vaccination")
        schedule.every().day.do(call_command, "import_dataset", "gendarmerie")
        print("Scheduler started")
        while True:
            schedule.run_pending()
            time.sleep(1)
