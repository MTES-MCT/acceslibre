import logging

from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.db import DatabaseError

from compte.models import EmailToken
from core import mattermost

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Supprime les demandes de changements d'emails non utilisés de plus de 24h"

    def handle(self, *args, **options):
        try:
            nb_deleted, _ = EmailToken.objects.filter(
                expire_at__lt=datetime.now(timezone.utc)
            ).delete()
            if nb_deleted > 0:
                mattermost.send(
                    f"{nb_deleted} outdated activation tokens deleted", tags=[__name__]
                )
        except DatabaseError as err:
            msg = f"Error encountered while purging outdated activation tokens: {err}"
            logger.error(msg)
            mattermost.send(msg, tags=[__name__])
