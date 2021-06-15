import schedule
import time

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        schedule.every().day.at("04:00").do(call_command, "purge_inactive_accounts")
        schedule.every().hour.do(call_command, "purge_tokens")
        schedule.every(3).hours.do(call_command("notify_changed_erps", hours=3))
        if settings.DATAGOUV_API_KEY:
            schedule.every().day.at("01:00").do(call_command, "export_to_datagouv")
        schedule.every().hour.do(call_command, "import_dataset", "vaccination")
        schedule.every().day.do(call_command, "import_dataset", "gendarmerie")
        schedule.every().day.at("01:00").do(call_command, "export_to_datagouv")
        print("Scheduler started")
        while True:
            schedule.run_pending()
            time.sleep(1)
