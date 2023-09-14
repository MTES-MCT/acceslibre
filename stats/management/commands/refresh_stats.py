import datetime
import logging

from django.core.management import BaseCommand, CommandError
from django.db.models import Q

from stats.models import Challenge, GlobalStats

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Calcule les statistiques globales affichées sur la page Statistiques et les stats des challenge en cours"

    def handle(self, *args, **options):
        try:
            GlobalStats.objects.get().refresh_stats()
            logger.info("STATS updated succesfully")
        except KeyboardInterrupt:
            raise CommandError("Interrompu.")

        # Compute challenges stats
        today = datetime.datetime.today()

        for challenge in Challenge.objects.filter(
            Q(
                start_date__gt=today,
            )
            | Q(start_date__lte=today, end_date__gt=today)
        ):
            try:
                challenge.refresh_stats()
                logger.info(f"STATS for challenge {challenge} updated")
            except KeyboardInterrupt:
                raise CommandError("Interrompu.")
