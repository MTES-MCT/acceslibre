import pytest
from django.test import Client
from django.urls import reverse
from django_registration.backends.activation.views import RegistrationView

from tests.factories import UserFactory


@pytest.fixture(autouse=True)
def no_brevo_sync(mocker):
    mocker.patch("compte.signals.sync_user_attributes.delay")


@pytest.fixture
def inactive_user():
    return UserFactory(username="johndoe", email="john@doe.com", is_active=False)


def activate(user, next_url):
    activation_key = RegistrationView().get_activation_key(user)
    url = reverse("django_registration_activate")
    return Client().post(f"{url}?next={next_url}", data={"activation_key": activation_key})


@pytest.mark.django_db
@pytest.mark.parametrize(
    "next_url",
    ["https://evil.example/", "//evil.example/", "http://evil.example/phishing"],
)
def test_activation_rejects_external_next(inactive_user, next_url):
    response = activate(inactive_user, next_url)

    inactive_user.refresh_from_db()
    assert inactive_user.is_active is True
    assert "evil.example" not in response.url
    assert response.wsgi_request.user.is_anonymous


@pytest.mark.django_db
def test_activation_keeps_internal_next(inactive_user):
    response = activate(inactive_user, "/contact/")

    inactive_user.refresh_from_db()
    assert inactive_user.is_active is True
    assert response.url == "/contact/"
    assert response.wsgi_request.user == inactive_user
