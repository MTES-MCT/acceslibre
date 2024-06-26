from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.mailer import BrevoMailer
from erp.models import Erp


class Command(BaseCommand):
    def _sync_users(self, since):
        users = User.objects.filter(last_login__gte=since)
        for user in users:
            BrevoMailer().sync_user(user)

    def _sync_erps(self, since):
        erps = Erp.objects.filter(created_at__gte=since, source=Erp.SOURCE_TALLY, import_email__isnull=False)
        for erp in erps:
            BrevoMailer().sync_erp(erp)

    def handle(self, *args, **options):
        since = timezone.now() - timedelta(days=20)
        self._sync_users(since)
        self._sync_erps(since)
