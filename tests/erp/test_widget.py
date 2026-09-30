import pytest
from django.urls import reverse
from django.utils import translation

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
