import logging
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils import timezone

from core.mailer import BrevoMailer
from erp import versioning
from subscription.models import ErpSubscription

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Envoie des notifications aux propriétaires de fiches Erp en cas de modifications effectuées par un tiers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours",
            type=int,
            default=3,
            help="Nombre d'heures entre deux envois de notification (default: 3)",
        )
        parser.add_argument(
            "--now",
            type=str,
            help="Temps courant au format ISO (ex. 2021-01-01 12:00:00)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Afficher les erreurs",
        )

    def send_notification(self, notification):
        recipient = notification.pop("user")
        return BrevoMailer().send_email(
            [recipient.email],
            template="changed_erp_notification",
            context={
                "username": recipient.username,
                "erps": notification["erps"],
                "url_changed_erp_notification": reverse("mes_contributions_recues"),
            },
        )

    def get_notifications(self, hours, now=None):
        notifications = {}
        notified_erp_user = []
        for version in versioning.get_recent_contribs_qs(hours, now):
            erp = versioning.extract_online_erp(version)
            if not erp:
                continue
            subscribers = [sub.user for sub in ErpSubscription.objects.subscribers(erp)]
            if not subscribers:
                continue
            for user in subscribers:
                if (erp.pk, user.pk) in notified_erp_user:
                    continue

                # retrieve history for this erp, excluding current subscriber
                changes_by_others = erp.get_history(exclude_changes_from=user)
                if not changes_by_others:
                    continue

                for change in changes_by_others:
                    change["user"] = change["user"].username
                    del change["date"]

                if user.pk not in notifications:
                    notifications[user.pk] = {"user": user, "erps": []}

                if erp not in notifications[user.pk]["erps"]:
                    notifications[user.pk]["erps"].append(
                        {
                            "code_postal": erp.code_postal,
                            "commune": erp.commune,
                            "nom": erp.nom,
                            "get_absolute_url": erp.get_absolute_url(),
                            "changes_by_others": changes_by_others,
                            "url_unsubscribe": reverse("unsubscribe_erp", kwargs={"erp_slug": erp.slug}),
                        }
                    )
                notified_erp_user.append((erp.pk, user.pk))

        return notifications

    def handle(self, *args, **options):
        if not settings.REAL_USER_NOTIFICATION:
            print("Launched only if settings.REAL_USER_NOTIFICATION is True.")
            return

        if options["now"]:
            now = datetime.fromisoformat(options["now"])
        else:
            now = timezone.now()

        notifications = self.get_notifications(options["hours"], now=now).values()
        sent_ok = 0
        for notification in notifications:
            sent_ok += 1 if self.send_notification(notification) else 0
        if notifications:
            logger.info(f"[CRON] {sent_ok}/{len(notifications)} notification(s) de souscription envoyée(s)")
        else:
            logger.info("No notif to send")
