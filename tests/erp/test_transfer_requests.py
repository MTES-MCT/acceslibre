from datetime import timedelta
from unittest.mock import ANY, PropertyMock

import pytest
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from erp.models import Accessibilite, Erp, ErpTransferRequest
from erp.transfer_requests import (
    TEMPLATE_TRANSFER_EXPIRY_OLD_OWNER,
    TEMPLATE_TRANSFER_REFUSED_NEW_OWNER,
    TEMPLATE_TRANSFER_REMINDER,
    TEMPLATE_TRANSFER_REQUEST,
    TEMPLATE_TRANSFER_SUCCESS_NEW_OWNER,
    TEMPLATE_TRANSFER_SUCCESS_OLD_OWNER,
    get_transfer_context,
    perform_transfer,
    refuse_transfer,
)
from tests.factories import ErpFactory, UserFactory


def make_rpa_erp(old_owner=None):
    return ErpFactory(user=old_owner or UserFactory(), checked_up_to_date_at=timezone.now())


def make_real_rpa_erp(old_owner=None):
    erp = ErpFactory(user=old_owner or UserFactory(), with_accessibility=True)
    erp.user_type = Erp.USER_ROLE_GESTIONNAIRE
    erp.rpa_exemption = True
    erp.checked_up_to_date_at = timezone.now()
    erp.save()
    # completion_rate is recomputed by a post_save signal, so it has to be forced with a queryset update
    Accessibilite.objects.filter(pk=erp.accessibilite.pk).update(completion_rate=100)
    erp.accessibilite.refresh_from_db()
    assert erp.rpa is True, f"erp {erp.pk} should be RPA"
    return erp


def make_transfer_request(erp=None, new_owner=None, old_owner=None, **kwargs):
    created_at = kwargs.pop("created_at", None)
    erp = erp or make_rpa_erp(old_owner=old_owner)
    transfer_request = ErpTransferRequest.objects.create(
        erp=erp,
        previous_manager=old_owner or erp.user,
        new_manager=new_owner or UserFactory(),
        **kwargs,
    )
    if created_at is not None:
        # created_at is a auto_now_add field, it can only be set after creation
        transfer_request.created_at = created_at
        transfer_request.save(update_fields=["created_at"])
    return transfer_request


def subscription_exists(user, erp):
    from subscription.models import ErpSubscription

    return ErpSubscription.objects.filter(user=user, erp=erp).exists()


@pytest.mark.django_db
class TestTransferHelpers:
    def test_get_transfer_context(self):
        transfer_request = make_transfer_request()
        context = get_transfer_context(transfer_request)

        assert context["erp_name"] == transfer_request.erp.nom
        assert context["url_accept"].endswith("?action=accept")
        assert context["url_refuse"].endswith("?action=refuse")
        assert context["url_response"] == context["url_accept"].split("?", 1)[0]
        assert "/contact/" in context["url_contact"]
        assert context["previous_manager_username"] == transfer_request.previous_manager.username
        assert context["new_manager_username"] == transfer_request.new_manager.username
        # Brevo templates use uppercase params (e.g. {{ params.USERNAME }})
        assert context["USERNAME"] == transfer_request.previous_manager.username
        assert context["NEW_USERNAME"] == transfer_request.new_manager.username
        assert context["ERP_URL"] == context["url_erp"]
        assert context["URL_ACCEPT"] == context["url_accept"]
        assert context["URL_REFUSE"] == context["url_refuse"]
        assert context["URL_RESPONSE"] == context["url_response"]
        assert context["ERP_NAME"] == transfer_request.erp.nom

    def test_perform_transfer(self, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        transfer_request = make_transfer_request()
        erp = transfer_request.erp
        initial_date = erp.checked_up_to_date_at

        assert perform_transfer(transfer_request) is True
        transfer_request.refresh_from_db()
        erp.refresh_from_db()

        assert erp.user == transfer_request.new_manager
        assert erp.user_type == Erp.USER_ROLE_GESTIONNAIRE
        # checked_up_to_date_at must stay unchanged when ownership is transferred
        assert erp.checked_up_to_date_at == initial_date
        assert transfer_request.status == ErpTransferRequest.STATUS_ACCEPTED
        assert transfer_request.responded_at is not None
        assert subscription_exists(transfer_request.new_manager, erp)
        assert mock_mail.call_count == 2
        mock_mail.assert_any_call(
            to_list=[transfer_request.new_manager.email],
            template=TEMPLATE_TRANSFER_SUCCESS_NEW_OWNER,
            context=ANY,
        )
        mock_mail.assert_any_call(
            to_list=[transfer_request.previous_manager.email],
            template=TEMPLATE_TRANSFER_SUCCESS_OLD_OWNER,
            context=ANY,
        )

    def test_perform_transfer_with_stale_instances_processes_once(self, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        transfer_request = make_transfer_request()
        stale_request = ErpTransferRequest.objects.get(pk=transfer_request.pk)

        assert perform_transfer(transfer_request) is True
        assert perform_transfer(stale_request) is False

        transfer_request.refresh_from_db()
        assert transfer_request.status == ErpTransferRequest.STATUS_ACCEPTED
        assert mock_mail.call_count == 2

    def test_perform_transfer_keeps_real_rpa_status(self, mocker):
        mocker.patch("core.mailer.BrevoMailer.send_email")
        erp = make_real_rpa_erp()
        transfer_request = make_transfer_request(erp=erp, old_owner=erp.user)

        assert perform_transfer(transfer_request) is True

        erp.refresh_from_db()
        assert erp.user == transfer_request.new_manager
        assert erp.rpa is True

    def test_only_one_pending_request_per_erp(self):
        transfer_request = make_transfer_request()

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ErpTransferRequest.objects.create(
                    erp=transfer_request.erp,
                    previous_manager=transfer_request.previous_manager,
                    new_manager=UserFactory(),
                )

        transfer_request.status = ErpTransferRequest.STATUS_REFUSED
        transfer_request.save(update_fields=["status"])
        ErpTransferRequest.objects.create(
            erp=transfer_request.erp,
            previous_manager=transfer_request.previous_manager,
            new_manager=UserFactory(),
        )

    def test_perform_transfer_expired_uses_expiration_template(self, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        transfer_request = make_transfer_request()

        assert perform_transfer(transfer_request, expired=True) is True
        transfer_request.refresh_from_db()

        assert transfer_request.status == ErpTransferRequest.STATUS_EXPIRED
        assert mock_mail.call_count == 2
        mock_mail.assert_any_call(
            to_list=[transfer_request.previous_manager.email],
            template=TEMPLATE_TRANSFER_EXPIRY_OLD_OWNER,
            context=ANY,
        )
        mock_mail.assert_any_call(
            to_list=[transfer_request.new_manager.email],
            template=TEMPLATE_TRANSFER_SUCCESS_NEW_OWNER,
            context=ANY,
        )

    def test_perform_transfer_non_pending_returns_false(self, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        transfer_request = make_transfer_request(status=ErpTransferRequest.STATUS_REFUSED)

        assert perform_transfer(transfer_request) is False
        transfer_request.refresh_from_db()
        assert transfer_request.status == ErpTransferRequest.STATUS_REFUSED
        assert not mock_mail.called

    def test_refuse_transfer(self, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        transfer_request = make_transfer_request()
        erp = transfer_request.erp

        assert refuse_transfer(transfer_request) is True
        transfer_request.refresh_from_db()
        erp.refresh_from_db()

        assert transfer_request.status == ErpTransferRequest.STATUS_REFUSED
        assert transfer_request.responded_at is not None
        # the current owner stays in place
        assert erp.user == transfer_request.previous_manager
        mock_mail.assert_called_once_with(
            to_list=[transfer_request.new_manager.email],
            template=TEMPLATE_TRANSFER_REFUSED_NEW_OWNER,
            context=ANY,
        )


@pytest.mark.django_db
class TestTransferErpView:
    def test_transfer_erp_creates_request_and_emails(self, client, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        mocker.patch("erp.models.Erp.rpa", new_callable=PropertyMock, return_value=True)
        new_owner = UserFactory()
        old_owner = UserFactory()
        erp = make_rpa_erp(old_owner=old_owner)
        client.force_login(new_owner)

        response = client.post(reverse("transfer_erp", kwargs={"erp_slug": erp.slug}))

        transfer_request = ErpTransferRequest.objects.get(erp=erp)
        assert response.status_code == 200
        assert transfer_request.previous_manager == old_owner
        assert transfer_request.new_manager == new_owner
        assert transfer_request.status == ErpTransferRequest.STATUS_PENDING
        mock_mail.assert_called_once_with(
            to_list=[old_owner.email],
            template=TEMPLATE_TRANSFER_REQUEST,
            context=ANY,
        )

    def test_transfer_erp_email_failure_deletes_request(self, client, mocker):
        mocker.patch("erp.models.Erp.rpa", new_callable=PropertyMock, return_value=True)
        mocker.patch("core.mailer.BrevoMailer.send_email", return_value=False)
        new_owner = UserFactory()
        old_owner = UserFactory()
        erp = make_rpa_erp(old_owner=old_owner)
        client.force_login(new_owner)

        response = client.post(reverse("transfer_erp", kwargs={"erp_slug": erp.slug}))

        assert response.status_code == 302
        assert not ErpTransferRequest.objects.filter(erp=erp).exists()

    def test_transfer_erp_without_current_manager_redirects(self, client, mocker):
        mocker.patch("erp.models.Erp.rpa", new_callable=PropertyMock, return_value=True)
        erp = make_rpa_erp(old_owner=UserFactory())
        erp.user = None
        erp.save(update_fields=["user"])
        client.force_login(UserFactory())

        response = client.post(reverse("transfer_erp", kwargs={"erp_slug": erp.slug}))

        assert response.status_code == 302
        assert not ErpTransferRequest.objects.filter(erp=erp).exists()

    def test_transfer_erp_non_rpa_redirects_with_error(self, client):
        erp = make_rpa_erp()
        client.force_login(UserFactory())

        response = client.post(reverse("transfer_erp", kwargs={"erp_slug": erp.slug}))

        assert response.status_code == 302
        assert not ErpTransferRequest.objects.filter(erp=erp).exists()

    def test_transfer_erp_already_owner_redirects_with_warning(self, client, mocker):
        mocker.patch("erp.models.Erp.rpa", new_callable=PropertyMock, return_value=True)
        user = UserFactory()
        erp = make_rpa_erp(old_owner=user)
        client.force_login(user)

        response = client.post(reverse("transfer_erp", kwargs={"erp_slug": erp.slug}))

        assert response.status_code == 302
        assert not ErpTransferRequest.objects.filter(erp=erp).exists()

    def test_transfer_erp_already_pending_redirects(self, client, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        mocker.patch("erp.models.Erp.rpa", new_callable=PropertyMock, return_value=True)
        transfer_request = make_transfer_request()
        client.force_login(UserFactory())

        response = client.post(reverse("transfer_erp", kwargs={"erp_slug": transfer_request.erp.slug}))

        assert response.status_code == 302
        assert ErpTransferRequest.objects.filter(erp=transfer_request.erp).count() == 1
        assert mock_mail.call_count == 0

    def test_transfer_erp_requires_post_and_login(self, client):
        erp = make_rpa_erp()

        response = client.post(reverse("transfer_erp", kwargs={"erp_slug": erp.slug}))
        assert response.status_code == 302
        assert "login" in response.url.split("?")[0]


@pytest.mark.django_db
class TestTransferErpResponseView:
    def test_get_response_page(self, client):
        transfer_request = make_transfer_request()

        response = client.get(reverse("transfer_erp_response", kwargs={"token": transfer_request.token}))

        assert response.status_code == 200
        assert transfer_request.status == ErpTransferRequest.STATUS_PENDING

    def test_accept_via_post(self, client, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        transfer_request = make_transfer_request()
        erp = transfer_request.erp
        initial_date = erp.checked_up_to_date_at

        response = client.post(
            reverse("transfer_erp_response", kwargs={"token": transfer_request.token}),
            {"action": "accept"},
        )

        assert response.status_code == 200
        erp.refresh_from_db()
        assert erp.user == transfer_request.new_manager
        assert erp.user_type == Erp.USER_ROLE_GESTIONNAIRE
        assert erp.checked_up_to_date_at == initial_date
        assert mock_mail.call_count == 2

    def test_accept_via_get_link_does_not_transfer(self, client, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        transfer_request = make_transfer_request()
        erp = transfer_request.erp

        response = client.get(
            f"{reverse('transfer_erp_response', kwargs={'token': transfer_request.token})}?action=accept"
        )

        assert response.status_code == 200
        transfer_request.refresh_from_db()
        erp.refresh_from_db()
        assert transfer_request.status == ErpTransferRequest.STATUS_PENDING
        assert erp.user == transfer_request.previous_manager
        assert not mock_mail.called

    def test_refuse_via_get_link_does_not_refuse(self, client, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        transfer_request = make_transfer_request()

        response = client.get(
            f"{reverse('transfer_erp_response', kwargs={'token': transfer_request.token})}?action=refuse"
        )

        assert response.status_code == 200
        transfer_request.refresh_from_db()
        assert transfer_request.status == ErpTransferRequest.STATUS_PENDING
        assert not mock_mail.called

    def test_refuse_via_post(self, client, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        transfer_request = make_transfer_request()
        erp = transfer_request.erp

        response = client.post(
            reverse("transfer_erp_response", kwargs={"token": transfer_request.token}),
            {"action": "refuse"},
        )

        assert response.status_code == 200
        transfer_request.refresh_from_db()
        erp.refresh_from_db()
        assert transfer_request.status == ErpTransferRequest.STATUS_REFUSED
        assert erp.user == transfer_request.previous_manager
        mock_mail.assert_called_once_with(
            to_list=[transfer_request.new_manager.email],
            template=TEMPLATE_TRANSFER_REFUSED_NEW_OWNER,
            context=ANY,
        )

    def test_already_processed_is_idempotent(self, client, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        transfer_request = make_transfer_request()
        erp = transfer_request.erp

        client.post(
            reverse("transfer_erp_response", kwargs={"token": transfer_request.token}),
            {"action": "accept"},
        )
        mock_mail.reset_mock()
        response = client.post(
            reverse("transfer_erp_response", kwargs={"token": transfer_request.token}),
            {"action": "refuse"},
        )

        assert response.status_code == 200
        transfer_request.refresh_from_db()
        erp.refresh_from_db()
        assert transfer_request.status == ErpTransferRequest.STATUS_ACCEPTED
        assert erp.user == transfer_request.new_manager
        assert not mock_mail.called

    def test_invalid_token_returns_404(self, client):
        response = client.get(
            reverse("transfer_erp_response", kwargs={"token": "00000000-0000-0000-0000-000000000000"})
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestProcessErpTransferRequestsCommand:
    def test_sends_reminder_after_one_week_only_once(self, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        transfer_request = make_transfer_request(created_at=timezone.now() - timedelta(days=8))

        call_command("process_erp_transfer_requests", now=(timezone.now() + timedelta(minutes=1)).isoformat())
        call_command("process_erp_transfer_requests", now=(timezone.now() + timedelta(minutes=2)).isoformat())

        transfer_request.refresh_from_db()
        assert transfer_request.status == ErpTransferRequest.STATUS_PENDING
        assert transfer_request.reminder_sent_at is not None
        mock_mail.assert_called_once_with(
            to_list=[transfer_request.previous_manager.email],
            template=TEMPLATE_TRANSFER_REMINDER,
            context=ANY,
        )

    def test_reminder_not_marked_sent_on_email_failure(self, mocker):
        mocker.patch(
            "erp.management.commands.process_erp_transfer_requests.send_transfer_reminder_to_old_owner",
            return_value=False,
        )
        transfer_request = make_transfer_request(created_at=timezone.now() - timedelta(days=8))

        call_command("process_erp_transfer_requests", now=(timezone.now() + timedelta(minutes=1)).isoformat())

        transfer_request.refresh_from_db()
        assert transfer_request.status == ErpTransferRequest.STATUS_PENDING
        assert transfer_request.reminder_sent_at is None

    def test_expires_after_two_weeks(self, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        transfer_request = make_transfer_request(created_at=timezone.now() - timedelta(days=15))

        call_command("process_erp_transfer_requests", now=(timezone.now() + timedelta(minutes=1)).isoformat())

        transfer_request.refresh_from_db()
        transfer_request.erp.refresh_from_db()
        assert transfer_request.status == ErpTransferRequest.STATUS_EXPIRED
        assert transfer_request.erp.user == transfer_request.new_manager
        assert mock_mail.call_count == 2
        mock_mail.assert_any_call(
            to_list=[transfer_request.previous_manager.email],
            template=TEMPLATE_TRANSFER_EXPIRY_OLD_OWNER,
            context=ANY,
        )

    def test_does_not_remind_an_expired_request(self, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        make_transfer_request(created_at=timezone.now() - timedelta(days=15))

        call_command("process_erp_transfer_requests", now=(timezone.now() + timedelta(minutes=1)).isoformat())

        # the weekly reminder must not be sent for an expired request
        reminder_calls = [c for c in mock_mail.call_args_list if c.kwargs["template"] == TEMPLATE_TRANSFER_REMINDER]
        assert reminder_calls == []

    def test_does_not_act_on_fresh_request(self, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        transfer_request = make_transfer_request()

        call_command("process_erp_transfer_requests")

        transfer_request.refresh_from_db()
        assert transfer_request.status == ErpTransferRequest.STATUS_PENDING
        assert transfer_request.reminder_sent_at is None
        assert not mock_mail.called


def test_transfer_request_status_is_readonly_in_admin():
    from erp.admin import ErpTransferRequestAdmin

    assert "status" in ErpTransferRequestAdmin.readonly_fields
