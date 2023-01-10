import logging
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Supprime les comptes jamais activés depuis un certain nombre de jours ou plus (par défaut: 30)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Nombre de jours (default: 30)",
        )
        parser.add_argument(
            "--today",
            type=str,
            help="Date de référence au format ISO (ex. 2021-01-01)",
        )

    def handle(self, *args, **options):
        if options["today"]:
            today = datetime.fromisoformat(options["today"])
        else:
            today = timezone.now()
        outdated_qs = (
            get_user_model()
            .objects.annotate(erps_count=Count("erp"))
            .filter(
                last_login=None,
                date_joined__lt=today - timedelta(days=options["days"]),
                erps_count=0,
            )
        )
        nb_deleted, _ = outdated_qs.delete()
        logger.info(f"[CRON] {nb_deleted} user account deleted.")
