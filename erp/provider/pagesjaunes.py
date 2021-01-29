import os
import requests

from core.lib import text


BASE_URL = "https://api.pagesjaunes.fr"


def get_auth_token():
    client_id = os.environ.get("PAGESJAUNES_API_CLIENT_KEY")
    client_secret = os.environ.get("PAGESJAUNES_API_SECRET_KEY")
    if not client_id or not client_secret:
        raise RuntimeError("No valid pagesjaunes API credentials available")
    res = requests.post(
        f"{BASE_URL}/oauth/client_credential/accesstoken",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    json = res.json()
    return json["access_token"]


def parse_result(result):
    infos = result["inscriptions"][0]
    (numero, voie) = text.extract_numero_voie(infos.get("address_street"))

    return dict(
        actif=True,
        source="pagesjaunes",
        source_id=result.get("merchant_id"),
        nom=result.get("merchant_name"),
        numero=numero,
        voie=voie,
        code_postal=infos.get("address_zipcode"),
        commune=infos.get("address_city"),
        code_insee=None,
        coordonnees=[infos.get("longitude"), infos.get("latitude")],
        naf=None,
        activite=None,
        siret=None,
        lieu_dit=None,
        contact_email=None,
        telephone=None,
        site_internet=None,
    )


def deduplicate_results(results):
    seen_ids = []
    processed_results = []
    for r in results:
        if r["source_id"] in seen_ids:
            continue
        seen_ids.append(r["source_id"])
        processed_results.append(r)
    return processed_results


def search(what, where):
    try:
        auth_token = get_auth_token()
        res = requests.get(
            f"{BASE_URL}/v1/pros/search",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={
                "what": what,
                "where": where,
            },
        )
        json = res.json()
        results = []
        for result in json["search_results"]["listings"]:
            results.append(parse_result(result))
        return deduplicate_results(results)
    except requests.exceptions.RequestException as err:
        raise RuntimeError(f"pagesjaunes api error: {err}")
