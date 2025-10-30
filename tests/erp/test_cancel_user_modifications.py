import pytest
import reversion
from django.core.management import call_command
from django.urls import reverse

from erp.models import Erp
from tests.factories import ErpFactory, UserFactory


@pytest.mark.django_db
def test_will_revert_user_created_erp(django_app):
    bad_user = UserFactory()
    with reversion.create_revision():
        reversion.set_user(bad_user)
        ErpFactory(with_accessibility=True)
    assert Erp.objects.count() == 1

    # Dry run
    call_command("cancel_user_modifications", bad_user.email, write=False)
    assert Erp.objects.count() == 1

    # Real run
    call_command("cancel_user_modifications", bad_user.email, write=True)
    assert not Erp.objects.exists()


@pytest.mark.django_db
def test_will_revert_user_changes(django_app):
    with reversion.create_revision():
        erp = ErpFactory(with_accessibility=True)
    assert Erp.objects.count() == 1

    good_user = UserFactory()
    response = django_app.get(reverse("contrib_transport", kwargs={"erp_slug": erp.slug}), user=good_user)
    form = response.forms[1]
    form["transport_station_presence"].value = "True"
    form["transport_information"] = "Pas loin du métro république"
    form.submit("Publier")

    bad_user = UserFactory()
    response = django_app.get(reverse("contrib_transport", kwargs={"erp_slug": erp.slug}), user=bad_user)
    form = response.forms[1]
    form["transport_station_presence"].value = "False"
    form["transport_information"] = ""
    form.submit("Publier")

    erp.refresh_from_db()
    assert erp.accessibilite.transport_station_presence is False
    assert erp.accessibilite.transport_information == ""

    # Dry run
    call_command("cancel_user_modifications", bad_user.email, write=False)
    erp = Erp.objects.get()
    assert erp.accessibilite.transport_station_presence is False
    assert erp.accessibilite.transport_information == ""

    # Real run
    call_command("cancel_user_modifications", bad_user.email, write=True)
    erp = Erp.objects.get()
    assert erp.accessibilite.transport_station_presence is True
    assert erp.accessibilite.transport_information == "Pas loin du métro république"


@pytest.mark.django_db
def test_will_not_revert_user_changes_when_edited(django_app):
    erp = ErpFactory(with_accessibility=True)
    assert Erp.objects.count() == 1

    good_user = UserFactory()
    response = django_app.get(reverse("contrib_transport", kwargs={"erp_slug": erp.slug}), user=good_user)
    form = response.forms[1]
    form["transport_station_presence"].value = "True"
    form["transport_information"] = "Pas loin du métro république"
    form.submit("Publier")

    bad_user = UserFactory()
    response = django_app.get(reverse("contrib_transport", kwargs={"erp_slug": erp.slug}), user=bad_user)
    form = response.forms[1]
    form["transport_station_presence"].value = "False"
    form["transport_information"] = ""
    form.submit("Publier")

    good_user = UserFactory()
    response = django_app.get(reverse("contrib_transport", kwargs={"erp_slug": erp.slug}), user=good_user)
    form = response.forms[1]
    form["transport_station_presence"].value = "True"
    form["transport_information"] = "Pas loin du métro république"
    form.submit("Publier")

    erp.refresh_from_db()
    assert erp.accessibilite.transport_station_presence is True
    assert erp.accessibilite.transport_information == "Pas loin du métro république"

    call_command("cancel_user_modifications", bad_user.email, write=True)
    erp = Erp.objects.get()
    assert erp.accessibilite.transport_station_presence is True
    assert erp.accessibilite.transport_information == "Pas loin du métro république"


@pytest.mark.django_db
def test_will_not_revert_user_changes_when_confirmed(django_app):
    erp = ErpFactory(with_accessibility=True)
    assert Erp.objects.count() == 1

    good_user = UserFactory()
    response = django_app.get(reverse("contrib_transport", kwargs={"erp_slug": erp.slug}), user=good_user)
    form = response.forms[1]
    form["transport_station_presence"].value = "True"
    form["transport_information"] = "Pas loin du métro république"
    form.submit("Publier")

    bad_user = UserFactory()
    response = django_app.get(reverse("contrib_transport", kwargs={"erp_slug": erp.slug}), user=bad_user)
    form = response.forms[1]
    form["transport_station_presence"].value = "False"
    form["transport_information"] = ""
    form.submit("Publier")

    erp.confirm_up_to_date(user=None)
    erp.refresh_from_db()

    call_command("cancel_user_modifications", bad_user.email, write=True)
    erp = Erp.objects.get()
    assert erp.accessibilite.transport_station_presence is False
    assert erp.accessibilite.transport_information == ""
