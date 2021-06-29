from datetime import datetime, timezone, timedelta
import logging
from typing import List

from django.conf import settings
from django.core.management.base import BaseCommand

from core import mailer, mattermost
from erp.models import Erp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Envoie une notification de rappel aux utilisateurs ayant commencé le remplissage d'une fiche sans la "
        "publier"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Afficher les erreurs",
        )

    def handle(self, *args, **options):
        now = datetime.now(timezone.utc)

        notifications = self.get_notifications(options["hours"], now=now).values()
        total = len(notifications)
        sent_ok = 0
        for notification in notifications:
            sent_ok += 1 if self.send_notification(notification) else 0
        if total > 0:
            plural = "s" if total > 1 else ""
            mattermost.send(
                f"{sent_ok}/{total} relance{plural} d'ERPs non-publiés",
                tags=[__name__],
            )

    def send_notification(self, notification):
        recipient, erp = notification
        return mailer.send_email(
            [recipient.email],
            f"[{settings.SITE_NAME}] Rappel: publiez votre ERP !",
            "mail/unpublished_erps_notification.txt",
            {
                "user": recipient,
                "erp": erp,
                "SITE_NAME": settings.SITE_NAME,
                "SITE_ROOT_URL": settings.SITE_ROOT_URL,
            },
        )

    def get_notifications(self, now=datetime.now(timezone.utc)):
        notifications = []
        erps: List[Erp] = Erp.objects.filter(
            published=False, updated_at__gt=now + timedelta(days=7)
        )

        for erp in erps:
            user = erp.user
            # todo check user preferences
            notifications.append((user, erp))

        return notifications
