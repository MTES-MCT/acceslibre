import pytest
from django.urls import reverse

from tests.factories import ErpFactory


@pytest.mark.django_db
def test_sitemap_erp_scales_properly(client, django_assert_max_num_queries):
    erp = ErpFactory()
    with django_assert_max_num_queries(23):
        response = client.get(reverse("sitemap", kwargs={"section": "erps"}))
        assert response.status_code == 200
        assert response.content is not None

    for _ in range(20):
        ErpFactory(
            nom="Erp",
            activite=erp.activite,
            published=True,
            commune="Jacou",
            commune_ext=erp.commune_ext,
        )

    with django_assert_max_num_queries(23):
        response = client.get(reverse("sitemap", kwargs={"section": "erps"}))
        assert response.status_code == 200
        assert response.content is not None
