import schedule
import time

from django.core.management.base import BaseCommand

from erp.jobs import check_closed_erps, purge_accounts
from erp.jobs.import_gendarmerie import ImportGendarmerie
from subscription.jobs import notify_changed_erps
from erp.jobs.import_centres_vaccination import ImportVaccinationsCenters


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        schedule.every().day.at("00:00").do(check_closed_erps.job, verbose=True)
        schedule.every().day.at("04:00").do(purge_accounts.job, verbose=True)
        schedule.every(notify_changed_erps.HOURS_CHECK).hours.do(
            notify_changed_erps.job, verbose=True
        )
        schedule.every().hour.do(
            ImportVaccinationsCenters(is_scheduler=True).job, verbose=True
        )
        schedule.every().week.do(ImportGendarmerie(is_scheduler=True).job, verbose=True)
        print("Scheduler started")
        while True:
            schedule.run_pending()
            time.sleep(1)
