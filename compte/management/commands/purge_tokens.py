import logging
from datetime import timezone

from django.core.management.base import BaseCommand

from compte.models import EmailToken

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Supprime les demandes de changements d'emails non utilisés de plus de 24h"

    def handle(self, *args, **options):
        nb_deleted, _ = EmailToken.objects.filter(expire_at__lt=timezone.now()).delete()
        logger.info(f"[CRON] Purge tokens, {nb_deleted} token(s) deleted")
