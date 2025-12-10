from erp.tasks import compute_access_completion_rate
from tests.factories import ActiviteFactory, ErpFactory, AccessibiliteFactory
from pytest import mark


@mark.django_db
def test_compute_completion_rate():
    erp = ErpFactory(activite=ActiviteFactory(slug="boulangerie"))
    access = AccessibiliteFactory(erp=erp, cheminement_ext_presence=False)

    compute_access_completion_rate(erp.accessibilite.pk)

    erp.accessibilite.refresh_from_db()
    assert erp.accessibilite.completion_rate == 5

    access.cheminement_ext_presence = True
    access.save()
    compute_access_completion_rate(erp.accessibilite.pk)

    erp.accessibilite.refresh_from_db()
    assert erp.accessibilite.completion_rate == 4
