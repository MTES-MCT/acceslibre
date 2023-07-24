from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from erp.management.commands.convert_tally_to_schema import Command as CommandConvertTallyToSchema
from erp.management.commands.notify_daily_draft import Command as CommandNotifyDailyDraft
from tests.factories import ErpFactory


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
