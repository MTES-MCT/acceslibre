import logging
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils import timezone

from core.mailer import BrevoMailer
from erp.models import Erp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    now = timezone.now()
    help = (
        "Envoie une notification de rappel aux utilisateurs ayant commencé le remplissage d'une fiche sans la publier"
    )

    def __init__(self, *args, **kwargs):
        if kwargs.get("now"):
            self.now = kwargs["now"]
            del kwargs["now"]
        super().__init__(*args, **kwargs)

    def handle(self, *args, **options):
        if not settings.REAL_USER_NOTIFICATION:
            print("Launched only if settings.REAL_USER_NOTIFICATION is True.")
            return

        notifications = self.get_notifications()
        sent_ok = 0
        for notification in notifications:
            sent_ok += 1 if self.send_notification(notification) else 0

        logger.info(f"{sent_ok}/{len(notifications)} relance(s) d'ERP(s) non-publié(s)")

    def get_notifications(self):
        notifications = {}
        since = self.now - timedelta(days=settings.UNPUBLISHED_ERP_NOTIF_DAYS)
        erps = Erp.objects.select_related("user").filter(
            published=False,
            user__isnull=False,
            user__is_active=True,
            user__preferences__notify_on_unpublished_erps=True,
            updated_at__lte=since,
        )
        for erp in erps.iterator(chunk_size=2000):
            erp_updated_since_days = (self.now - erp.updated_at).days
            if erp_updated_since_days >= settings.UNPUBLISHED_ERP_NOTIF_DAYS:
                if erp.user.pk not in notifications:
                    notifications[erp.user.pk] = {"user": erp.user, "erps": []}
                erp_as_dict = {
                    "commune": erp.commune,
                    "activite": erp.activite.nom,
                    "slug": erp.slug,
                    "nom": erp.nom,
                    "url_publication": reverse("contrib_publication", kwargs={"erp_slug": erp.slug}),
                }
                notifications[erp.user.pk]["erps"].append(erp_as_dict)
        return [n for n in notifications.values() if n["erps"]]

    def send_notification(self, notification):
        user, erps = notification["user"], notification["erps"]
        return BrevoMailer().send_email(
            to_list=[user.email],
            template="notif_weekly_unpublished",
            context={
                "username": user.username,
                "erps": erps,
                "url_mes_erps_draft": f"{reverse('mes_erps')}?published=0",
                "url_mes_preferences": reverse("mes_preferences"),
            },
        )
