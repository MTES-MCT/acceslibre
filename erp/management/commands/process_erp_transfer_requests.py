import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from erp.models import ErpTransferRequest
from erp.transfer_requests import (
    perform_transfer,
    send_transfer_reminder_to_old_owner,
)

logger = logging.getLogger(__name__)

TRANSFER_REMINDER_DAYS = 7
TRANSFER_EXPIRATION_DAYS = 14


class Command(BaseCommand):
    help = (
        "Relance le gestionnaire actuel 1 semaine après une demande de changement de gestionnaire, "
        "puis effectue le transfert passé un délai de 2 semaines sans réponse."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--now",
            type=str,
            help="Temps courant au format ISO (ex. 2021-01-01 12:00:00)",
        )

    def handle(self, *args, **options):
        if options["now"]:
            now = datetime.fromisoformat(options["now"])
        else:
            now = timezone.now()

        self.expire_requests(now)
        self.send_reminders(now)

    def expire_requests(self, now):
        threshold = now - timedelta(days=TRANSFER_EXPIRATION_DAYS)
        pending = ErpTransferRequest.objects.select_related("erp", "previous_manager", "new_manager").filter(
            status=ErpTransferRequest.STATUS_PENDING,
            created_at__lte=threshold,
        )
        for transfer_request in pending:
            perform_transfer(transfer_request, expired=True)
            logger.info(
                f"[CRON] Ownership transfer by expiry for erp {transfer_request.erp.nom}, "
                f"request #{transfer_request.pk}"
            )

    def send_reminders(self, now):
        threshold = now - timedelta(days=TRANSFER_REMINDER_DAYS)
        pending = ErpTransferRequest.objects.select_related("erp", "previous_manager", "new_manager").filter(
            status=ErpTransferRequest.STATUS_PENDING,
            reminder_sent_at__isnull=True,
            created_at__lte=threshold,
        )
        for transfer_request in pending:
            send_transfer_reminder_to_old_owner(transfer_request)
            transfer_request.reminder_sent_at = now
            transfer_request.save(update_fields=["reminder_sent_at"])
            logger.info(f"[CRON] Reminder sent for request #{transfer_request.pk} on erp {transfer_request.erp.nom}")
