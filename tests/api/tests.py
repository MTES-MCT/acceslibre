import json

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url, status_code",
    [
        (reverse("openapi-schema"), 200),
        (reverse("apidocs"), 200),
        (reverse("api-root"), 200),
        (reverse("accessibilite-list"), 200),
        (reverse("accessibilite-help"), 200),
        (reverse("activite-list"), 200),
        (reverse("activite-list") + "?commune=Foo", 200),
        (reverse("erp-list"), 200),
    ],
)
def test_api_urls_ok(url, status_code, api_client):
    response = api_client.get(url)

    assert response.status_code == status_code


def test_endpoint_erp_list(data, api_client):
    response = api_client.get(reverse("erp-list"))

    content = json.loads(response.content)
    assert content["count"] == 1
    assert content["page_size"] == 20
    erp_json = content["results"][0]
    assert erp_json["nom"] == "Aux bons croissants"
    assert erp_json["activite"]["nom"] == "Boulangerie"
    assert erp_json["activite"]["slug"] == "boulangerie"
    assert erp_json["code_postal"] == "34830"
    assert "user" not in erp_json
    assert erp_json["accessibilite"]["transport"]["transport_station_presence"] is None

    # same request with clean
    response = api_client.get(reverse("erp-list") + "?clean=true")
    content = json.loads(response.content)
    assert content["count"] == 1
    assert content["page_size"] == 20
    erp_json = content["results"][0]
    assert erp_json["nom"] == "Aux bons croissants"
    assert "transport" not in erp_json["accessibilite"]
    assert erp_json["accessibilite"]["accueil"]["sanitaires_presence"] is True
    assert erp_json["accessibilite"]["accueil"]["sanitaires_adaptes"] is False

    # same request with readable
    response = api_client.get(reverse("erp-list") + "?readable=true")
    content = json.loads(response.content)
    erp_json = content["results"][0]
    assert (
        erp_json["accessibilite"]["datas"]["accueil"]["sanitaires_presence"]
        == "Des sanitaires sont mis à disposition dans l'établissement"
    )
    assert (
        erp_json["accessibilite"]["datas"]["accueil"]["sanitaires_adaptes"]
        == "Aucun sanitaire adapté mis à disposition dans l'établissement"
    )
    assert erp_json["accessibilite"]["datas"]["transport"]["transport_station_presence"] is None

    # same request with readable & clean
    response = api_client.get(reverse("erp-list") + "?readable=true&clean=true")
    content = json.loads(response.content)
    erp_json = content["results"][0]
    assert (
        erp_json["accessibilite"]["datas"]["accueil"]["sanitaires_presence"]
        == "Des sanitaires sont mis à disposition dans l'établissement"
    )
    assert (
        erp_json["accessibilite"]["datas"]["accueil"]["sanitaires_adaptes"]
        == "Aucun sanitaire adapté mis à disposition dans l'établissement"
    )
    assert "transport" not in erp_json["accessibilite"]["datas"]


def test_endpoint_erp_list_qs(data, api_client):
    response = api_client.get(reverse("erp-list") + "?q=croissants")
    content = json.loads(response.content)
    assert len(content["results"]) == 1

    response = api_client.get(reverse("erp-list") + "?q=nexiste_pas")
    content = json.loads(response.content)
    assert len(content["results"]) == 0
