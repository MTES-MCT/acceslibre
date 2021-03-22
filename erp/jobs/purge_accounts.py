import logging

from datetime import timedelta
from django.utils import timezone

from django.contrib.auth import get_user_model


logger = logging.getLogger(__name__)


def job(*args, **kwargs):
    today = kwargs["today"] if "today" in kwargs else timezone.now()
    outdated_qs = get_user_model().objects.filter(
        is_active=False,
        date_joined__lt=today - timedelta(days=30),
    )

    (nb_deleted, _) = outdated_qs.delete()
    if nb_deleted > 0:
        logger.info(f"{nb_deleted} comptes utilisateur obsolètes supprimés.")
