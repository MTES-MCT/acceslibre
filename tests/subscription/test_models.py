import pytest

from subscription.models import ErpSubscription
from tests.factories import ErpFactory, UserFactory


@pytest.mark.django_db
def test_subscribe():
    erp = ErpFactory()
    sophie = UserFactory()

    assert ErpSubscription.objects.count() == 0

    ErpSubscription.subscribe(erp, sophie)

    assert ErpSubscription.objects.count() == 1
    assert ErpSubscription.objects.filter(user=sophie, erp=erp).count() == 1

    ErpSubscription.subscribe(erp, sophie)

    assert ErpSubscription.objects.count() == 1
    assert ErpSubscription.objects.filter(user=sophie, erp=erp).count() == 1


@pytest.mark.django_db
def test_unsubscribe():
    erp = ErpFactory()
    sophie = UserFactory()

    assert ErpSubscription.objects.count() == 0

    ErpSubscription.subscribe(erp, sophie)

    assert ErpSubscription.objects.count() == 1

    ErpSubscription.unsubscribe(erp, sophie)

    assert ErpSubscription.objects.count() == 0


@pytest.mark.django_db
def test_Erp_is_subscribed_by():
    erp = ErpFactory()
    sophie = UserFactory()

    assert erp.is_subscribed_by(sophie) is False

    ErpSubscription.subscribe(erp, sophie)

    assert erp.is_subscribed_by(sophie) is True
