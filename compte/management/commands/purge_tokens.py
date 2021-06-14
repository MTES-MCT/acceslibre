import logging

from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.db import DatabaseError

from compte.models import EmailToken


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Supprime les demandes de changements d'emails non utilisés de plus de 24h"

    def handle(self, *args, **options):
        try:
            EmailToken.objects.filter(expire_at__lt=datetime.now(timezone.utc)).delete()
        except DatabaseError as err:
            logger.error(
                f"Error when deleting unused email change activation tokens: {err}"
            )
            raise DatabaseError
