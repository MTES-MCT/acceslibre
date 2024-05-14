from uuid import uuid4

import pytest
from django.core.management import call_command

from erp.models import Erp
from tests.factories import ErpFactory


@pytest.mark.django_db
def test_remove_duplicates():
    erp = ErpFactory(with_accessibilite=True)
    access = erp.accessibilite

    erp.pk = None
    erp.uuid = uuid4()
    erp.save()

    access.pk = None
    access.erp = erp
    access.save()

    call_command("remove_duplicates", write=True)
    assert Erp.objects.count() == 1


@pytest.mark.django_db
def test_remove_duplicates_accent_insensitive():
    erp = ErpFactory(with_accessibilite=True, nom="Name with accents : éèï")
    access = erp.accessibilite

    erp.pk = None
    erp.uuid = uuid4()
    erp.nom = "Name with accents : eei"
    erp.save()

    access.pk = None
    access.erp = erp
    access.save()

    call_command("remove_duplicates", write=True)
    assert Erp.objects.count() == 1
