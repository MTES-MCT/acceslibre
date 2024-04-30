from django.urls import reverse

from erp.models import Erp


def test_sitemap_erp_scales_properly(data, client, django_assert_max_num_queries):
    with django_assert_max_num_queries(23):
        response = client.get(reverse("sitemap", kwargs={"section": "erps"}))
        assert response.status_code == 200
        assert response.content is not None

    for i in range(20):
        Erp.objects.create(
            nom="Erp",
            activite=data.erp.activite,
            published=True,
            commune="Jacou",
            commune_ext=data.erp.commune_ext,
        )

    with django_assert_max_num_queries(23):
        response = client.get(reverse("sitemap", kwargs={"section": "erps"}))
        assert response.status_code == 200
        assert response.content is not None
