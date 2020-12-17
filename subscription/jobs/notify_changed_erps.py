from django.conf import settings

# from django.contrib.auth import get_user_model

from core import mailer

from erp import versioning
from subscription.models import ErpSubscription

HOURS_CHECK = 3


def send_notification(user, erps):
    mailer.send_email(
        [user.email],
        f"[{settings.SITE_NAME}] Vous avez reçu de nouvelles contributions",
        "mail/changed_erp_notification.txt",
        {
            "user": user,
            "erps": erps,
            "SITE_NAME": settings.SITE_NAME,
            "SITE_ROOT_URL": settings.SITE_ROOT_URL,
        },
    )


def get_notifications(hours, now=None):
    notifications = {}
    versions = [
        version
        for version in versioning.get_recent_contribs_qs(hours, now)
        if hasattr(version, "content_type")  # no idea how/why this is happening :/
    ]
    for version in versions:
        erp = versioning.extract_online_erp(version)
        if not erp:
            continue
        subscribers = [sub.user for sub in ErpSubscription.objects.subscribers(erp)]
        if len(subscribers) == 0:
            continue
        for user in subscribers:
            # retrieve history for this erp, excluding current subscriber
            changes_by_others = [
                diff for diff in erp.get_history() if diff["user"] != user
            ]
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
        send_notification(notification["user"], notification["erps"])
