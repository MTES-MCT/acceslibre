import uuid
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone

from erp.management.commands.convert_tally_to_schema import Command as CommandConvertTallyToSchema
from erp.management.commands.notify_daily_draft import Command as CommandNotifyDailyDraft
from erp.models import Erp
from tests.factories import AccessibiliteFactory, ErpFactory, UserFactory


class TestConvertTallyToSchema:
    @pytest.mark.parametrize(
        "line, expected_line",
        (
            pytest.param(
                {
                    "Est-ce qu’il y au moins une place handicapé dans votre parking ?": "Oui, nous avons une place handicapé",
                    "cp": "4100",
                    "adresse": "7 grande rue, Saint Martin en Haut",
                    "Combien de marches y a-t-il pour entrer dans votre établissement ?": "124",
                    "email": "contrib@beta.gouv.fr",
                },
                {
                    "stationnement_presence": True,
                    "stationnement_pmr": True,
                    "code_postal": "04100",
                    "code_insee": "04100",
                    "lieu_dit": None,
                    "numero": "7",
                    "voie": "Grande rue",
                    "commune": "Saint Martin en Haut",
                    "entree_marches": 124,
                    "import_email": "contrib@beta.gouv.fr",
                },
                id="nominal_case",
            ),
        ),
    )
    def test_process_line(self, line, expected_line):
        assert CommandConvertTallyToSchema()._process_line(line) == expected_line


class TestNotifyDraft:
    @override_settings(REAL_USER_NOTIFICATION=True)
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "creation_date, published, should_send_email",
        (
            pytest.param(
                timezone.now() - timedelta(days=1, hours=2),
                False,
                False,
                id="too_old",
            ),
            pytest.param(
                timezone.now() - timedelta(minutes=55),
                False,
                False,
                id="too_recent",
            ),
            pytest.param(
                timezone.now() - timedelta(days=1),
                False,
                True,
                id="already_published",
            ),
            pytest.param(
                timezone.now() - timedelta(days=1),
                True,
                False,
                id="ok",
            ),
        ),
    )
    def test_handle(self, mocker, creation_date, published, should_send_email):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        erp = ErpFactory(published=published)
        erp.created_at = creation_date  # cannot be set on factory params, as it is a auto_now_add attr
        erp.save()

        CommandNotifyDailyDraft().handle()

        assert mock_mail.call_count == int(should_send_email)

        if should_send_email:
            mock_mail.assert_called_once_with(
                to_list=erp.user.email,
                subject=None,
                template="draft",
                context={"publish_url": f"/contrib/publication/{erp.slug}/"},
            )


@pytest.mark.django_db
def test_remove_duplicates_with_same_accessibility_data():
    main_erp = AccessibiliteFactory(erp__nom="Mairie de Lyon").erp

    duplicate = main_erp
    duplicate.pk = None
    duplicate.uuid = uuid.uuid4()
    duplicate.nom = "Mairie - Lyon"
    duplicate.save()

    duplicate_access = main_erp.accessibilite
    duplicate_access.pk = None
    duplicate_access.erp = duplicate
    duplicate_access.save()

    assert Erp.objects.count() == 2

    call_command("remove_duplicate_mairie", write=True)

    assert Erp.objects.count() == 1


@pytest.mark.django_db
def test_merge_and_remove_duplicates_with_different_accessibility_data():
    main_erp = AccessibiliteFactory(stationnement_presence=None, erp__nom="Mairie de Lyon").erp

    duplicate = main_erp
    duplicate.pk = None
    duplicate.uuid = uuid.uuid4()
    duplicate.nom = "Mairie - Lyon"
    duplicate.save()

    duplicate_access = main_erp.accessibilite
    duplicate_access.pk = None
    duplicate_access.erp = duplicate
    duplicate_access.stationnement_presence = True
    duplicate_access.save()

    assert Erp.objects.count() == 2

    call_command("remove_duplicate_mairie", write=True)

    assert Erp.objects.count() == 1
    assert Erp.objects.get().accessibilite.stationnement_presence is True


@pytest.mark.django_db
def test_leave_untouched_multiple_duplicates():
    main_erp = AccessibiliteFactory(erp__nom="Mairie de Lyon").erp

    for _ in range(0, 3):
        duplicate = main_erp
        duplicate.pk = None
        duplicate.source = Erp.SOURCE_PUBLIC
        duplicate.uuid = uuid.uuid4()
        duplicate.nom = "Mairie - Lyon"
        duplicate.save()

        duplicate_access = main_erp.accessibilite
        duplicate_access.pk = None
        duplicate_access.erp = duplicate
        duplicate_access.stationnement_presence = True
        duplicate_access.save()

    assert Erp.objects.count() == 4

    out = StringIO()
    call_command("remove_duplicate_mairie", write=True, stderr=out)

    assert Erp.objects.count() == 4
    # Every ERP will be checked for duplicates, printing 4 messages
    assert (
        out.getvalue()
        == """3 ERPs found - Need to improve merge strategy in this case
3 ERPs found - Need to improve merge strategy in this case
3 ERPs found - Need to improve merge strategy in this case
3 ERPs found - Need to improve merge strategy in this case\n"""
    )
