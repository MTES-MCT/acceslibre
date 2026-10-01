from datetime import datetime, timezone

import pytest
from django.test import override_settings

from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from erp.models import Accessibilite, Erp, ExternalSource
from tests.factories import AccessibiliteFactory, ErpFactory, ExternalSourceFactory, UserFactory

REMOVE_LABEL = "Supprimer l'image"
CHANGE_LABEL = "Changer la photo"
ADD_LABEL = "Ajouter une photo"


def make_rpa_erp():
    erp = ErpFactory(user=UserFactory(), with_accessibility=True)
    erp.user_type = Erp.USER_ROLE_GESTIONNAIRE
    erp.rpa_exemption = True
    erp.checked_up_to_date_at = datetime.now(timezone.utc)
    erp.save()
    # completion_rate is recomputed by a post_save signal, so it has to be forced with a queryset update
    Accessibilite.objects.filter(pk=erp.accessibilite.pk).update(completion_rate=100)
    erp.accessibilite.refresh_from_db()
    assert erp.rpa is True, f"erp {erp.pk} should be RPA"
    return erp


def add_panoramax_image(erp):
    return ExternalSourceFactory(erp=erp, source=ExternalSource.SOURCE_PANORAMAX, source_id="image-id|1.0,2.0")


def get_visible_buttons(client, erp):
    url = erp.get_absolute_url()
    response = client.get(url)
    assert response.status_code == 200, f"unexpected status {response.status_code} on {url}"
    content = response.content.decode()
    return [label for label in (REMOVE_LABEL, CHANGE_LABEL, ADD_LABEL) if label in content]


@pytest.mark.django_db
def test_panoramax_change_button_hidden_for_rpa_not_owner(client):
    erp = make_rpa_erp()
    add_panoramax_image(erp)
    client.force_login(UserFactory())

    buttons = get_visible_buttons(client, erp)

    assert buttons == [], f"no button expected on a RPA erp without rights, got {buttons}"


@pytest.mark.django_db
def test_panoramax_change_button_visible_for_rpa_owner(client):
    erp = make_rpa_erp()
    add_panoramax_image(erp)
    client.force_login(erp.user)

    buttons = get_visible_buttons(client, erp)

    assert buttons == [CHANGE_LABEL], f"the owner should only get the change button, got {buttons}"


@pytest.mark.django_db
def test_panoramax_add_button_hidden_for_rpa_not_owner(client):
    erp = make_rpa_erp()

    with override_settings(PANORAMAX_OPENED_CITIES=[erp.commune]):
        client.force_login(UserFactory())
        buttons = get_visible_buttons(client, erp)

    assert buttons == [], f"no button expected on a RPA erp without rights, got {buttons}"


@pytest.mark.django_db
def test_panoramax_add_button_visible_for_rpa_owner(client):
    erp = make_rpa_erp()

    with override_settings(PANORAMAX_OPENED_CITIES=[erp.commune]):
        client.force_login(erp.user)
        buttons = get_visible_buttons(client, erp)

    assert buttons == [ADD_LABEL], f"the owner should only get the add button, got {buttons}"


@pytest.mark.django_db
def test_panoramax_remove_button_still_visible_for_staff_on_rpa_not_owner(client):
    erp = make_rpa_erp()
    add_panoramax_image(erp)
    client.force_login(UserFactory(is_staff=True))

    buttons = get_visible_buttons(client, erp)

    assert buttons == [REMOVE_LABEL], f"staff should only get the remove button, got {buttons}"


@pytest.mark.django_db
def test_panoramax_buttons_unchanged_for_non_rpa_erp(client):
    # with_accessibility is required: the ERP details page always reads erp.accessibilite
    erp = ErpFactory(user=UserFactory(), with_accessibility=True)
    add_panoramax_image(erp)
    assert erp.rpa is False, f"erp {erp.pk} should not be RPA"

    buttons = get_visible_buttons(client, erp)

    assert buttons == [CHANGE_LABEL], f"a non RPA erp should keep the change button, got {buttons}"


@pytest.fixture
def rpa_erp(mocker):
    mocker.patch("erp.models.Erp.rpa", return_value=True)
    return ErpFactory(user=UserFactory())


@pytest.mark.django_db
class TestCanBeModifiedBy:
    def test_rpa_not_authenticated_denied(self, rpa_erp):
        assert rpa_erp.can_be_modified_by(None) is False

    def test_rpa_anonymous_user_denied(self, rpa_erp):
        assert rpa_erp.can_be_modified_by(AnonymousUser()) is False

    def test_rpa_other_user_denied(self, rpa_erp):
        other = UserFactory()
        assert rpa_erp.can_be_modified_by(other) is False

    def test_rpa_owner_allowed(self, rpa_erp):
        assert rpa_erp.can_be_modified_by(rpa_erp.user) is True

    def test_non_rpa_any_user_allowed(self):
        owner = UserFactory()
        erp = ErpFactory(user=owner)
        assert erp.rpa is False
        assert erp.can_be_modified_by(None) is True
        assert erp.can_be_modified_by(UserFactory()) is True


@pytest.mark.django_db
@pytest.mark.parametrize(
    "route",
    [
        "panoramax_add",
        "contrib_edit_infos",
        "contrib_a_propos",
        "contrib_transport",
        "contrib_exterieur",
        "contrib_entree",
        "contrib_accueil",
        "contrib_commentaire",
        "contrib_publication",
        "contrib_completion_rate",
    ],
)
def test_contrib_view_rpa_not_owner_forbidden(client, mocker, route):
    mocker.patch("erp.models.Erp.rpa", return_value=True)
    erp = ErpFactory(user=UserFactory())
    client.force_login(UserFactory())
    response = client.get(reverse(route, kwargs={"erp_slug": erp.slug}))
    assert response.status_code == 403


@pytest.mark.django_db
def test_confirm_up_to_date_rpa_not_owner_unchanged(client, mocker):
    mocker.patch("erp.models.Erp.rpa", return_value=True)
    erp = ErpFactory(published=True, user=UserFactory())
    initial_date = erp.checked_up_to_date_at
    client.force_login(UserFactory())
    response = client.post(reverse("confirm_up_to_date", kwargs={"erp_slug": erp.slug}))
    assert response.status_code == 302
    erp.refresh_from_db()
    assert erp.checked_up_to_date_at == initial_date


@pytest.mark.django_db
def test_claim_rpa_not_owner_denied(client, mocker):
    mocker.patch("erp.models.Erp.rpa", return_value=True)
    owner = UserFactory()
    erp = ErpFactory(user=owner)
    attacker = UserFactory()
    client.force_login(attacker)
    response = client.post(reverse("claim", kwargs={"erp_slug": erp.slug}))
    assert response.status_code == 302
    erp.refresh_from_db()
    assert erp.user == owner


@pytest.mark.django_db
def test_claim_rpa_owner_allowed(client, mocker):
    mocker.patch("erp.models.Erp.rpa", return_value=True)
    owner = UserFactory()
    erp = ErpFactory(user=owner)
    client.force_login(owner)
    response = client.post(reverse("claim", kwargs={"erp_slug": erp.slug}))
    assert response.status_code == 302
    erp.refresh_from_db()
    assert erp.user == owner


@pytest.mark.django_db
def test_contribution_v2_rpa_not_owner_denied(client, mocker):
    mocker.patch("erp.models.Erp.rpa", return_value=True)
    erp = AccessibiliteFactory(erp__user=UserFactory(), entree_porte_presence=True).erp
    client.force_login(UserFactory())
    response = client.get(reverse("contribution-step", kwargs={"erp_slug": erp.slug, "step_number": 0}))
    assert response.status_code == 403


@pytest.mark.django_db
def test_contribution_v2_rpa_owner_allowed(client, mocker):
    mocker.patch("erp.models.Erp.rpa", return_value=True)
    owner = UserFactory()
    erp = AccessibiliteFactory(erp__user=owner, entree_porte_presence=True).erp
    client.force_login(owner)
    response = client.get(reverse("contribution-step", kwargs={"erp_slug": erp.slug, "step_number": 0}))
    assert response.status_code == 200
