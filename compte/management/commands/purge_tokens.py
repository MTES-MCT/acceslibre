import logging

from datetime import datetime, timezone

from django.core.management.base import BaseCommand, CommandError
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
                    f"{nb_deleted} jetons d'activation d'adresse email supprimés",
                    tags=[__name__],
                )
        except DatabaseError as err:
            raise CommandError(
                f"Erreur lors de la purge des jetons de changement d'adresse email: {err}"
            )
