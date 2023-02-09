import logging

from django.core.management.base import BaseCommand

from core.mailer import get_mailer
from erp.models import ActivitySuggestion

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Notify admins to manage non mapped activity suggestions"

    def handle(self, *args, **options):
        activity_suggestions = ActivitySuggestion.objects.filter(mapped_activity=None)
        if not activity_suggestions.count():
            return True

        get_mailer().mail_admins(
            "Nouvelles suggestions d'activités.",
            "mail/activity_suggestions_notification.txt",
        )
