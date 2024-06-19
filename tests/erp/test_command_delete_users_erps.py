import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.utils import timezone
from reversion.models import Revision, Version

from erp.models import Erp
from tests.factories import ErpFactory, UserFactory


@pytest.mark.django_db
def test_will_delete_users_erp():
    erp = ErpFactory(with_accessibilite=True)
    assert Erp.objects.count() == 1

    call_command("delete_users_erps", erp.user, write=False)
    assert Erp.objects.count() == 1

    call_command("delete_users_erps", erp.user, write=True)
    assert Erp.objects.count() == 0


@pytest.mark.django_db
def test_will_not_delete_users_erp_with_confirmation_date():
    erp = ErpFactory(with_accessibilite=True, checked_up_to_date_at=timezone.now())
    assert Erp.objects.count() == 1

    call_command("delete_users_erps", erp.user, write=True)
    assert Erp.objects.count() == 1


@pytest.mark.django_db
def test_will_not_delete_users_erp_with_revisions():
    erp = ErpFactory(with_accessibilite=True)
    assert Erp.objects.count() == 1

    other_user = UserFactory()
    erp_content_type = ContentType.objects.get_for_model(Erp)
    revision = Revision.objects.create(user=other_user, date_created=timezone.now())
    Version.objects.create(object_id=erp.id, content_type=erp_content_type, revision=revision)

    call_command("delete_users_erps", erp.user, write=True)
    assert Erp.objects.count() == 0
