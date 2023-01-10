import logging

from django.core.management import BaseCommand, CommandError

from stats.models import GlobalStats

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Calcule les statistiques globales affichées sur la page Statistiques"

    def handle(self, *args, **options):
        try:
            GlobalStats.objects.get().refresh_stats()
            logger.info("STATS updated succesfully")
        except KeyboardInterrupt:
            raise CommandError("Interrompu.")
