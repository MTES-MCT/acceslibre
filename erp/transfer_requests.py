import logging

import reversion
from django.conf import settings
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as translate

from core.mailer import BrevoMailer
from erp.models import Erp, ErpTransferRequest
from subscription.models import ErpSubscription

logger = logging.getLogger(__name__)

TEMPLATE_TRANSFER_REQUEST = "demande_transfer_ancien_gestionnaire"
TEMPLATE_TRANSFER_REMINDER = "demande_transfer_relance"
TEMPLATE_TRANSFER_SUCCESS_NEW_OWNER = "transfer_ok_nouveau_gestionnaire"
TEMPLATE_TRANSFER_SUCCESS_OLD_OWNER = "transfer_ok_ancien_gestionnaire"
TEMPLATE_TRANSFER_EXPIRY_OLD_OWNER = "transfer_ok_expiration_ancien_gestionnaire"
TEMPLATE_TRANSFER_REFUSED_NEW_OWNER = "transfer_ko_nouveau_gestionnaire"


def _absolute_url(path):
    return f"{settings.SITE_ROOT_URL}{path}"


def get_transfer_context(transfer_request):
    erp = transfer_request.erp
    return {
        "erp_name": erp.nom,
        "commune": erp.commune,
        "url_erp": _absolute_url(erp.get_absolute_url()),
        "url_contrib": _absolute_url(reverse("contrib_edit_infos", kwargs={"erp_slug": erp.slug})),
        "url_contact": _absolute_url(
            reverse("contact_topic_erp", kwargs={"topic": "signalement", "erp_slug": erp.slug})
        ),
        "url_response": _absolute_url(reverse("transfer_erp_response", kwargs={"token": transfer_request.token})),
        "url_accept": _absolute_url(
            reverse("transfer_erp_response", kwargs={"token": transfer_request.token}) + "?action=accept"
        ),
        "url_refuse": _absolute_url(
            reverse("transfer_erp_response", kwargs={"token": transfer_request.token}) + "?action=refuse"
        ),
        "previous_manager_username": transfer_request.previous_manager.username,
        "new_manager_username": transfer_request.new_manager.username,
    }


def send_transfer_request_to_old_owner(transfer_request):
    return BrevoMailer().send_email(
        to_list=[transfer_request.previous_manager.email],
        template=TEMPLATE_TRANSFER_REQUEST,
        context=get_transfer_context(transfer_request),
    )


def send_transfer_reminder_to_old_owner(transfer_request):
    return BrevoMailer().send_email(
        to_list=[transfer_request.previous_manager.email],
        template=TEMPLATE_TRANSFER_REMINDER,
        context=get_transfer_context(transfer_request),
    )


def send_transfer_success_to_new_owner(transfer_request):
    return BrevoMailer().send_email(
        to_list=[transfer_request.new_manager.email],
        template=TEMPLATE_TRANSFER_SUCCESS_NEW_OWNER,
        context=get_transfer_context(transfer_request),
    )


def send_transfer_success_to_old_owner(transfer_request):
    return BrevoMailer().send_email(
        to_list=[transfer_request.previous_manager.email],
        template=TEMPLATE_TRANSFER_SUCCESS_OLD_OWNER,
        context=get_transfer_context(transfer_request),
    )


def send_transfer_expiry_to_old_owner(transfer_request):
    return BrevoMailer().send_email(
        to_list=[transfer_request.previous_manager.email],
        template=TEMPLATE_TRANSFER_EXPIRY_OLD_OWNER,
        context=get_transfer_context(transfer_request),
    )


def send_transfer_refused_to_new_owner(transfer_request):
    return BrevoMailer().send_email(
        to_list=[transfer_request.new_manager.email],
        template=TEMPLATE_TRANSFER_REFUSED_NEW_OWNER,
        context=get_transfer_context(transfer_request),
    )


def perform_transfer(transfer_request, *, expired=False):
    """Assign the erp to the new manager, then send the confirmation emails."""
    if transfer_request.status != ErpTransferRequest.STATUS_PENDING:
        return False

    erp = transfer_request.erp
    with reversion.create_revision():
        erp.user = transfer_request.new_manager
        erp.user_type = Erp.USER_ROLE_GESTIONNAIRE
        erp.save()
        reversion.set_comment(
            translate("Changement de gestionnaire : {old} -> {new}").format(
                old=transfer_request.previous_manager.username,
                new=transfer_request.new_manager.username,
            )
        )

    ErpSubscription.subscribe(erp, transfer_request.new_manager)

    LogEntry.objects.create(
        user=transfer_request.new_manager,
        content_type=ContentType.objects.get_for_model(Erp),
        object_id=erp.id,
        object_repr=erp.nom,
        action_flag=CHANGE,
        change_message=("Changement de gestionnaire par expiration" if expired else "Changement de gestionnaire"),
    )

    transfer_request.status = ErpTransferRequest.STATUS_EXPIRED if expired else ErpTransferRequest.STATUS_ACCEPTED
    transfer_request.responded_at = timezone.now()
    transfer_request.save(update_fields=["status", "responded_at"])

    send_transfer_success_to_new_owner(transfer_request)
    if expired:
        send_transfer_expiry_to_old_owner(transfer_request)
    else:
        send_transfer_success_to_old_owner(transfer_request)
    return True


def refuse_transfer(transfer_request):
    """Refuse the request and notify the requester."""
    if transfer_request.status != ErpTransferRequest.STATUS_PENDING:
        return False

    transfer_request.status = ErpTransferRequest.STATUS_REFUSED
    transfer_request.responded_at = timezone.now()
    transfer_request.save(update_fields=["status", "responded_at"])

    send_transfer_refused_to_new_owner(transfer_request)
    return True
