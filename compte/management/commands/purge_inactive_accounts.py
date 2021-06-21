from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError
from django.db.models import Count
from django.utils import timezone

from core import mattermost


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
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Afficher les erreurs",
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
                is_active=False,
                date_joined__lt=today - timedelta(days=options["days"]),
                erps_count=0,
            )
        )
        try:
            nb_deleted, _ = outdated_qs.delete()
            if nb_deleted > 0:
                mattermost.send(
                    f"{nb_deleted} comptes utilisateur obsolètes supprimés.",
                    tags=[__name__],
                )
        except DatabaseError as err:
            raise CommandError(f"Erreur lors de la purge des comptes obslètes: {err}")
