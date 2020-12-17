from django.conf import settings

# from django.contrib.auth import get_user_model

from core import mailer

from erp import versioning
from subscription.models import ErpSubscription

HOURS_CHECK = 3


def send_notification(notification):
    recipient = notification["user"]
    mailer.send_email(
        [recipient.email],
        f"[{settings.SITE_NAME}] Vous avez reçu de nouvelles contributions",
        "mail/changed_erp_notification.txt",
        {
            "user": recipient,
            "erps": notification["erps"],
            "SITE_NAME": settings.SITE_NAME,
            "SITE_ROOT_URL": settings.SITE_ROOT_URL,
        },
    )


def get_notifications(hours, now=None):
    notifications = {}
    for version in versioning.get_recent_contribs_qs(hours, now):
        erp = versioning.extract_online_erp(version)
        if not erp:
            continue
        subscribers = [sub.user for sub in ErpSubscription.objects.subscribers(erp)]
        if len(subscribers) == 0:
            continue
        for user in subscribers:
            # retrieve history for this erp, excluding current subscriber
            changes_by_others = erp.get_history(exclude_changes_from=user)
            if len(changes_by_others) == 0:
                continue
            # expose changes_by_others to be used in template
            erp.changes_by_others = changes_by_others
            if user.pk not in notifications:
                notifications[user.pk] = {"user": user, "erps": []}
            if erp not in notifications[user.pk]["erps"]:
                notifications[user.pk]["erps"].append(erp)

    return notifications


def job(*args, **kwargs):
    notifications = get_notifications(hours=HOURS_CHECK)
    for notification in notifications.values():
        send_notification(notification)
