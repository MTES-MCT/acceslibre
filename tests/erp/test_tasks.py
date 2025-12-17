from pytest import mark

from erp.tasks import compute_access_completion_rate
from tests.factories import AccessibiliteFactory, ActiviteFactory, ActivitiesGroupFactory, ErpFactory


@mark.django_db
def test_compute_completion_rate():
    erp = ErpFactory(activite=ActiviteFactory(slug="boulangerie"))
    access = AccessibiliteFactory(erp=erp, cheminement_ext_presence=False)

    compute_access_completion_rate(access.pk)

    access.refresh_from_db()
    assert access.completion_rate == 5

    access.cheminement_ext_presence = True
    access.save()
    compute_access_completion_rate(access.pk)

    access.refresh_from_db()
    assert access.completion_rate == 4


@mark.django_db
def test_compute_completion_rate_hosting():
    activity = ActiviteFactory(slug="hotel", nom="Hôtel")
    ActivitiesGroupFactory(activities=[activity], name="Hébergement")
    erp = ErpFactory(activite=activity)
    access = AccessibiliteFactory(erp=erp, accueil_chambre_nombre_accessibles=None)

    compute_access_completion_rate(access.pk)

    assert "accueil_chambre_nombre_accessibles" in access.get_exposed_fields()
    access.refresh_from_db()
    assert access.completion_rate == 0

    access.accueil_chambre_nombre_accessibles = 1
    access.save()

    compute_access_completion_rate(access.pk)

    access.refresh_from_db()

    assert access.completion_rate == 3
