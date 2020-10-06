from django.conf import settings
from django.contrib.auth import get_user_model

from core import mailer

from erp import versioning


HOURS_CHECK = 3


def send_update_notification(owner, changes):
    mailer.send_email(
        [owner.email],
        f"[{settings.SITE_NAME}] Vous avez reçu de nouvelles contributions",
        "mail/changed_erp_notification.txt",
        {
            "owner": owner,
            "changes": changes,
            "SITE_NAME": settings.SITE_NAME,
            "SITE_ROOT_URL": settings.SITE_ROOT_URL,
        },
    )


def job(*args, **kwargs):
    User = get_user_model()
    owners = versioning.get_owners_to_notify(hours=HOURS_CHECK)
    for (owner_pk, changes) in owners.items():
        owner = User.objects.get(pk=owner_pk)
        send_update_notification(owner, changes)
