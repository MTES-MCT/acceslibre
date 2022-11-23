import datetime

from django.core.management import BaseCommand, CommandError
from django.db.models import Q

from stats.models import Challenge


class Command(BaseCommand):
    help = "Calcule les statistiques concernant les challenges en cours"

    def handle(self, *args, **options):
        today = datetime.datetime.today()

        for challenge in Challenge.objects.filter(
            Q(
                start_date__gt=today,
            )
            | Q(start_date__lte=today, end_date__gt=today)
        ):
            try:
                challenge.refresh_stats()
                print(f"STATS for challenge {challenge} update successfully")
            except KeyboardInterrupt:
                raise CommandError("Interrompu.")
