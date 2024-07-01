import logging
from datetime import timedelta

from django.core.management import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone
from sentry_sdk import monitor

from stats.models import Challenge

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Calcule les statistiques des challenge en cours"

    @monitor(monitor_slug="refresh_stats")
    def handle(self, *args, **options):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        for challenge in Challenge.objects.filter(
            Q(
                start_date__gt=today,
            )
            | Q(start_date__lte=today, end_date__gt=yesterday)  # We compute figures for day D-1
        ):
            try:
                challenge.refresh_stats()
                logger.info(f"STATS for challenge {challenge} updated")
            except KeyboardInterrupt:
                raise CommandError("Interrompu.")
