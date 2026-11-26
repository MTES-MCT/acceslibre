import pytest
from django.urls import reverse
from django.utils import translation

from erp.models import Accessibilite
from erp.widget_utils import (
    get_aire_de_jeux_label,
    get_douches_label,
    get_salle_consultation_label,
    get_soignant_label,
    get_tribunes_label,
    get_vestiaires_label,
)
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
    access = Accessibilite(accueil_soignant=accueil_soignant, accueil_soignant_experience=accueil_soignant_experience)

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


@pytest.mark.parametrize(
    "accueil_aire_de_jeux, expected_label",
    (
        (None, ""),
        (False, "Aire de jeux non accessible"),
        (True, "Aire de jeux accessible"),
    ),
)
def test_get_aire_de_jeux_label(accueil_aire_de_jeux, expected_label):
    access = Accessibilite(accueil_aire_de_jeux=accueil_aire_de_jeux)

    with translation.override("fr"):
        assert get_aire_de_jeux_label(access) == expected_label


@pytest.mark.parametrize(
    "presence, places, accompagnants, expected_label",
    (
        (None, None, None, ""),
        (False, None, None, "Pas de tribune"),
        (True, None, None, ""),
        (True, 0, None, "Tribunes non accessibles aux personnes en fauteuil roulant"),
        (True, 1, None, "1 place accessible aux personnes en fauteuils"),
        (True, 3, None, "3 places accessibles aux personnes en fauteuils"),
        (True, 3, 0, "3 places accessibles aux personnes en fauteuils sans place accompagnant"),
        (True, 3, 1, "3 places accessibles avec 1 place accompagnant"),
        (True, 3, 4, "3 places accessibles avec places accompagnants"),
    ),
)
def test_get_tribunes_label(presence, places, accompagnants, expected_label):
    access = Accessibilite(
        accueil_tribunes_presence=presence,
        accueil_tribunes_places=places,
        accueil_tribunes_places_avec_accompagnants=accompagnants,
    )

    with translation.override("fr"):
        assert get_tribunes_label(access) == expected_label


@pytest.mark.parametrize(
    "accueil_vestiaires, expected_label",
    (
        (None, ""),
        (False, "Vestiaires non accessibles"),
        (True, "Vestiaires accessibles"),
    ),
)
def test_get_vestiaires_label(accueil_vestiaires, expected_label):
    access = Accessibilite(accueil_vestiaires=accueil_vestiaires)

    with translation.override("fr"):
        assert get_vestiaires_label(access) == expected_label


@pytest.mark.parametrize(
    "individuelles_adaptees, collectives_adaptees, expected_label",
    (
        (None, None, ""),
        (None, True, ""),
        (True, None, "Douches individuelles accessibles"),
        (True, False, "Douches individuelles accessibles"),
        (False, None, ""),
        (False, False, "Douches non accessibles"),
        (False, True, "Douches collectives accessibles"),
    ),
)
def test_get_douches_label(individuelles_adaptees, collectives_adaptees, expected_label):
    access = Accessibilite(
        accueil_douches_individuelles_adaptees=individuelles_adaptees,
        accueil_douches_collectives_adaptees=collectives_adaptees,
    )

    with translation.override("fr"):
        assert get_douches_label(access) == expected_label


@pytest.mark.django_db
def test_widget_displays_sports_equipment_section(client):
    access = AccessibiliteFactory(
        accueil_aire_de_jeux=True,
        accueil_tribunes_presence=False,
        accueil_vestiaires=False,
        accueil_douches_individuelles=True,
        accueil_douches_individuelles_adaptees=True,
    )

    with translation.override("fr"):
        response = client.get(reverse("widget_erp_uuid", kwargs={"uuid": access.erp.uuid}))

    content = response.content.decode()
    assert "Équipements sportifs" in content
    assert "Aire de jeux accessible" in content
    assert "Pas de tribune" in content
    assert "Vestiaires non accessibles" in content
    assert "Douches individuelles accessibles" in content
    assert "equipements-sportifs-widget.png" in content


@pytest.mark.django_db
def test_widget_hides_sports_equipment_section_when_unknown(client):
    access = AccessibiliteFactory(accueil_aire_de_jeux=None)

    with translation.override("fr"):
        response = client.get(reverse("widget_erp_uuid", kwargs={"uuid": access.erp.uuid}))

    content = response.content.decode()
    assert "Équipements sportifs" not in content
    assert "equipements-sportifs-widget.png" not in content
