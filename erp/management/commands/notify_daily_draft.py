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
    help = "Send a transactionnal email to user having left an erp in a draft state."

    def handle(self, *args, **options):
        if not settings.REAL_USER_NOTIFICATION:
            print("Launched only if settings.REAL_USER_NOTIFICATION is True.")
            return

        yesterday = timezone.now() - timedelta(days=1, hours=1)
        one_hour_ago = timezone.now() - timedelta(hours=1)
        erps = Erp.objects.filter(created_at__gt=yesterday, created_at__lte=one_hour_ago, published=False).exclude(
            user=None
        )

        mailer = BrevoMailer()
        for erp in erps:
            mailer.send_email(
                to_list=erp.user.email,
                template="draft",
                context={"publish_url": reverse("contrib_publication", kwargs={"erp_slug": erp.slug})},
            )
