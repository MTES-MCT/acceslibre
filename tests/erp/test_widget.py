import pytest
from django.urls import reverse
from django.utils import translation

from erp.models import Accessibilite
from erp.widget_utils import get_salle_consultation_label, get_soignant_label
from tests.factories import AccessibiliteFactory


@pytest.mark.django_db
def test_get_widget(client, django_assert_max_num_queries):
    access = AccessibiliteFactory()

    with django_assert_max_num_queries(1):
        response = client.get(reverse("widget_erp_uuid", kwargs={"uuid": access.erp.uuid}))
        assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    "params, headers, expected_lang, expected_text",
    (
        ({}, {}, "fr", "Voir plus sur"),
        ({}, {"HTTP_ACCEPT_LANGUAGE": "en"}, "en", "See more on"),
        ({"lang": "en"}, {}, "en", "See more on"),
        ({"lang": "fr"}, {"HTTP_ACCEPT_LANGUAGE": "en"}, "fr", "Voir plus sur"),
        ({"lang": "xx"}, {"HTTP_ACCEPT_LANGUAGE": "en"}, "en", "See more on"),
    ),
)
def test_get_widget_language(client, params, headers, expected_lang, expected_text):
    access = AccessibiliteFactory()

    response = client.get(reverse("widget_erp_uuid", kwargs={"uuid": access.erp.uuid}), params, **headers)

    assert response.status_code == 200
    assert response.headers["Content-Language"] == expected_lang
    assert f'lang="{expected_lang}"' in response.content.decode()
    assert expected_text in response.content.decode()


@pytest.mark.django_db
def test_get_widget_language_on_404(client):
    response = client.get(reverse("widget_erp_uuid", kwargs={"uuid": "unknown"}), {"lang": "en"})

    assert response.headers["Content-Language"] == "en"
    assert 'lang="en"' in response.content.decode()


@pytest.mark.django_db
def test_widget_code_embeds_current_language():
    access = AccessibiliteFactory()

    with translation.override("en"):
        assert 'data-lang="en"' in access.erp.widget_code
        assert ">Accessibility</a>" in access.erp.widget_code


@pytest.mark.django_db
def test_widget_code_falls_back_on_default_language():
    access = AccessibiliteFactory()

    with translation.override(None):
        assert 'data-lang="fr"' in access.erp.widget_code


@pytest.mark.parametrize(
    "accueil_soignant, accueil_soignant_experience, expected_label",
    (
        (None, [], ""),
        (False, [], "Soignant non sensibilisé au handicap"),
        (True, [], "Soignant sensibilisé au handicap"),
        (True, None, "Soignant sensibilisé au handicap"),
        (True, ["auditif"], "Soignant sensibilisé au handicap : auditif"),
        (True, ["cognitif", "visuel", "auditif"], "Soignant sensibilisé au handicap : auditif, visuel, cognitif"),
    ),
)
def test_get_soignant_label(accueil_soignant, accueil_soignant_experience, expected_label):
    access = Accessibilite(
        accueil_soignant=accueil_soignant, accueil_soignant_experience=accueil_soignant_experience
    )

    with translation.override("fr"):
        assert get_soignant_label(access) == expected_label


@pytest.mark.parametrize(
    "accueil_salle_consultation_accessible, accueil_consultation_domicile, expected_label",
    (
        (None, None, ""),
        (None, True, ""),
        (True, None, "Salle de consultation accessible aux fauteuils roulants"),
        (True, False, "Salle de consultation accessible aux fauteuils roulants"),
        (False, None, "Salle de consultation non accessible"),
        (False, False, "Salle de consultation non accessible"),
        (False, True, "Salle de consultation non accessible. Consultations à domicile possibles."),
    ),
)
def test_get_salle_consultation_label(
    accueil_salle_consultation_accessible, accueil_consultation_domicile, expected_label
):
    access = Accessibilite(
        accueil_salle_consultation_accessible=accueil_salle_consultation_accessible,
        accueil_consultation_domicile=accueil_consultation_domicile,
    )

    with translation.override("fr"):
        assert get_salle_consultation_label(access) == expected_label
