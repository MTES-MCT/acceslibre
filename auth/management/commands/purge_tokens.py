import sys
from datetime import datetime

from django.core.management.base import BaseCommand

from auth.models import EmailToken


def fatal(msg):
    print(msg)
    sys.exit(1)


class Command(BaseCommand):
    help = "Supprime les demandes de changements d'emails non utilisés de plus de 24h"

    def handle(self, *args, **options):
        try:
            EmailToken.objects.filter(expire_at__lt=datetime.utcnow()).delete()
        except RuntimeError as err:
            fatal(err)
