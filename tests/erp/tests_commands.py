import pytest
from django.test import Client

from erp.models import Erp, Accessibilite


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user_create_erp(data):
    def _factory(user=data.niko, **a11y_data):
        example = {
            "source": "sirene",
            "source_id": "xxx",
            "nom": "niko erp",
            "recevant_du_public": True,
            "activite": data.boulangerie.pk,
            "siret": "21690266800013",
            "numero": "4",
            "voie": "Grand rue",
            "lieu_dit": "",
            "code_postal": "34830",
            "commune": "JACOU",
            "site_internet": "https://google.com/",
        }
        erp = Erp.objects.create(**example, user=user)
        if a11y_data:
            Accessibilite.objects.create(erp=erp, **a11y_data)
        else:
            # simulate the case we have a non-a11y field filled
            Accessibilite.objects.create(erp=erp, commentaire="simple commentaire")
        return erp

    return _factory


def test_notification_unpublished_erp(niko_create_erp):
    erp = niko_create_erp()
    # # sophie updates this erp data
    # client.force_login(data.sophie)
    # response = client.post(
    #     reverse("contrib_edit_infos", kwargs={"erp_slug": erp.slug}),
    #     data={
    #         "source": "sirene",
    #         "source_id": "xxx",
    #         "nom": "sophie erp",
    #         "recevant_du_public": True,
    #         "activite": data.boulangerie.pk,
    #         "siret": "21690266800013",
    #         "numero": "4",
    #         "voie": "Grand rue",
    #         "lieu_dit": "",
    #         "code_postal": "34830",
    #         "commune": "Jacou",
    #         "site_internet": "http://google.com/",
    #         "action": "contribute",
    #     },
    #     follow=True,
    # )
    #
    # assert response.status_code == 200
    # updated_erp = Erp.objects.get(slug=erp.slug)
    # assert response.context["form"].errors == {}
    # assert updated_erp.nom == "sophie erp"
    # assert Version.objects.count() != 0
    #
    # call_command("notify_changed_erps")
    # unsubscribe_url = reverse("unsubscribe_erp", kwargs={"erp_slug": erp.slug})
    #
    # assert len(mail.outbox) == 1
    # assert mail.outbox[0].to == [data.niko.email]
    # assert "Vous avez reçu de nouvelles contributions" in mail.outbox[0].subject
    # assert "sophie erp" in mail.outbox[0].body
    # assert "34830 Jacou" in mail.outbox[0].body
    # assert "sophie a mis à jour les informations suivantes" in mail.outbox[0].body
    # assert 'nom: "niko erp" devient "sophie erp"' in mail.outbox[0].body
    # assert f"{settings.SITE_ROOT_URL}{unsubscribe_url}" in mail.outbox[0].body
    # assert updated_erp.get_absolute_url() in mail.outbox[0].body
