import csv
import datetime
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from stats.queries import get_count_challenge


class Command(BaseCommand):
    help = "Exporte les joueurs du challenge DDT."

    def handle(self, *args, **options):
        start_date = datetime.datetime(2022, 3, 21)
        stop_date = datetime.datetime(2022, 6, 21, 23, 59, 59)
        top_contribs, total_contributions = get_count_challenge(start_date, stop_date)
        stamp = datetime.date.today().isoformat()
        csv_filename = f"export-challenge-{stamp}.csv"
        with open(os.path.join(settings.BASE_DIR, csv_filename), "w") as csvfile:
            fieldnames = ["Email", "Nom d'utilisateur", "ERPs publiés"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for player in top_contribs:
                writer.writerow(
                    {
                        "Email": player.email.lower(),
                        "Nom d'utilisateur": player.username,
                        "ERPs publiés": player.erp_count_published,
                    }
                )
