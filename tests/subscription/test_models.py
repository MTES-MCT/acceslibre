import pytest

from subscription.models import ErpSubscription


def test_subscribe(data):
    assert ErpSubscription.objects.count() == 0

    ErpSubscription.subscribe(data.erp, data.sophie)

    assert ErpSubscription.objects.count() == 1
    assert ErpSubscription.objects.filter(user=data.sophie, erp=data.erp).count() == 1

    ErpSubscription.subscribe(data.erp, data.sophie)

    assert ErpSubscription.objects.count() == 1
    assert ErpSubscription.objects.filter(user=data.sophie, erp=data.erp).count() == 1


def test_unsubscribe(data):
    assert ErpSubscription.objects.count() == 0

    ErpSubscription.subscribe(data.erp, data.sophie)

    assert ErpSubscription.objects.count() == 1

    ErpSubscription.unsubscribe(data.erp, data.sophie)

    assert ErpSubscription.objects.count() == 0


def test_Erp_is_subscribed_by(data):
    assert data.erp.is_subscribed_by(data.sophie) is False

    ErpSubscription.subscribe(data.erp, data.sophie)

    assert data.erp.is_subscribed_by(data.sophie) is True
