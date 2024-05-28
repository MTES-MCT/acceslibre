from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.mailer import BrevoMailer


class Command(BaseCommand):
    def handle(self, *args, **options):
        since = timezone.now() - timedelta(days=20)
        users = User.objects.filter(last_login__gte=since)
        for user in users:
            BrevoMailer().sync_user(user)
