import logging

from datetime import timedelta
from django.utils import timezone

from django.contrib.auth import get_user_model
from django.db.models import Count


logger = logging.getLogger(__name__)


def job(*args, **kwargs):
    """Purges never activated accounts, keeping ones having existing erps attached
    (in case a user has been deactivated after having contributed for example).
    """
    today = kwargs["today"] if "today" in kwargs else timezone.now()
    outdated_qs = (
        get_user_model()
        .objects.annotate(erps_count=Count("erp"))
        .filter(
            is_active=False,
            date_joined__lt=today - timedelta(days=30),
            erps_count=0,
        )
    )

    (nb_deleted, _) = outdated_qs.delete()
    if nb_deleted > 0:
        logger.info(f"{nb_deleted} comptes utilisateur obsolètes supprimés.")
