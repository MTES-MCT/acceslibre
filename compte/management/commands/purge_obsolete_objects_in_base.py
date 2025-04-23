import logging
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from compte.models import EmailToken

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Delete user account which have never been activated, in the last X days (30 by default)."
        "Delete expired email tokens. Delete expired internal API keys."
    )

    def _delete_users(self, options):
        if options["today"]:
            today = datetime.fromisoformat(options["today"])
        else:
            today = timezone.now()

        outdated_qs = (
            get_user_model()
            .objects.annotate(erps_count=Count("erp"))
            .annotate(challenges_count=Count("inscriptions"))
            .filter(
                last_login=None,
                date_joined__lt=today - timedelta(days=options["days"]),
                erps_count=0,
                challenges_count=0,
            )
        )
        nb_deleted, _ = outdated_qs.delete()
        logger.info(f"[CRON] Purge users, {nb_deleted} user account deleted.")

    def _delete_email_tokens(self):
        nb_deleted, _ = EmailToken.objects.filter(expire_at__lt=timezone.now()).delete()
        logger.info(f"[CRON] Purge tokens, {nb_deleted} token(s) deleted.")

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Nb days for users deletion (default: 30)",
        )
        parser.add_argument(
            "--today",
            type=str,
            help="Reference date, ISO format (ex. 2021-01-01)",
        )

    def handle(self, *args, **options):
        self._delete_users(options)
        self._delete_email_tokens()
