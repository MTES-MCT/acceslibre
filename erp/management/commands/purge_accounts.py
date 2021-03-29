import sys

from django.core.management.base import BaseCommand
from erp.jobs import purge_accounts


def fatal(msg):
    print(msg)
    sys.exit(1)


class Command(BaseCommand):
    help = "Supprime les comptes jamais activés depuis 30 jours ou plus."

    def handle(self, *args, **options):  # noqa
        try:
            purge_accounts.job()
        except RuntimeError as err:
            fatal(err)
