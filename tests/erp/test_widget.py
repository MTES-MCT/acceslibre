import pytest
from django.urls import reverse

from tests.factories import AccessibiliteFactory


@pytest.mark.django_db
def test_get_widget(client, django_assert_max_num_queries):
    access = AccessibiliteFactory()

    with django_assert_max_num_queries(1):
        response = client.get(reverse("widget_erp_uuid", kwargs={"uuid": access.erp.uuid}))
        assert response.status_code == 200
