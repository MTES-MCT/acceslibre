import logging

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from core import mailer, mattermost
from erp.models import Erp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    now = timezone.now()
    help = (
        "Envoie une notification de rappel aux utilisateurs ayant commencé le "
        "remplissage d'une fiche sans la publier"
    )

    def __init__(self, *args, **kwargs):
        if kwargs.get("now"):
            self.now = kwargs["now"]
            del kwargs["now"]
        super().__init__(*args, **kwargs)

    def handle(self, *args, **options):
        notifications = self.get_notifications()
        total = len(notifications)
        sent_ok = 0
        for notification in notifications:
            sent_ok += 1 if self.send_notification(notification) else 0
        if total > 0:
            plural = "s" if total > 1 else ""
            mattermost.send(
                f"{sent_ok}/{total} relance{plural} d'ERP{plural} non-publié{plural}",
                tags=[__name__],
            )

    def get_notifications(self):
        notifications = {}
        since = self.now - timedelta(days=settings.UNPUBLISHED_ERP_NOTIF_DAYS)
        erps = Erp.objects.select_related("user", "commune_ext").filter(
            published=False,
            user__isnull=False,
            user__is_active=True,
            user__preferences__notify_on_unpublished_erps=True,
            updated_at__lte=since,
        )
        for erp in erps:
            erp_updated_since_days = (self.now - erp.updated_at).days
            if erp_updated_since_days >= settings.UNPUBLISHED_ERP_NOTIF_DAYS:
                if erp.user.pk not in notifications:
                    notifications[erp.user.pk] = {"user": erp.user, "erps": []}
                notifications[erp.user.pk]["erps"].append(erp)
        return [n for _, n in notifications.items() if len(n["erps"]) > 0]

    def send_notification(self, notification):
        user, erps = notification["user"], notification["erps"]
        return mailer.send_email(
            [user.email],
            f"[{settings.SITE_NAME}] Des établissements sont en attente de publication",
            "mail/unpublished_erps_notification.txt",
            {
                "user": user,
                "erps": erps,
                "SITE_NAME": settings.SITE_NAME,
                "SITE_ROOT_URL": settings.SITE_ROOT_URL,
            },
        )
