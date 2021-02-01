import os
import requests
import time

from core.lib import text
from erp.models import Commune


BASE_URL = "https://api.pagesjaunes.fr"


class Client:
    """PageJaunes (SoLocal) API client.

    @see https://developer.pagesjaunes.fr/quickstart#quickstart
    """

    auth_token = None
    auth_token_last_fetched = None
    auth_token_ttl_seconds = None

    def __init__(self, client_id=None, client_secret=None):
        if client_id:
            self.client_id = client_id
        else:
            self.client_id = os.environ.get("PAGESJAUNES_API_CLIENT_KEY")
        if client_secret:
            self.client_secret = client_secret
        else:
            self.client_secret = os.environ.get("PAGESJAUNES_API_SECRET_KEY")
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Client needs client auth credentials")

    def get_auth_token(self, now=None):
        # If we have a valid token in memory, return it
        now = now or time.time()
        if (
            self.auth_token_last_fetched
            and self.auth_token
            and now - self.auth_token_last_fetched >= 3600
        ):
            return self.auth_token
        # Request auth token
        res = requests.post(
            f"{BASE_URL}/oauth/client_credential/accesstoken",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        self.auth_token_last_fetched = time.time()
        self.auth_token = res.json()["access_token"]
        return self.auth_token

    def parse_result(self, result):
        infos = result["inscriptions"][0]
        (numero, voie) = text.extract_numero_voie(infos.get("address_street"))
        photos = [p["url"] for p in result.get("visual_urls", [])]
        photo = photos[0] if len(photos) > 0 else None

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
            photo=photo,
        )

    def deduplicate_results(self, results):
        seen_ids = []
        processed_results = []
        for r in results:
            if r["source_id"] in seen_ids:
                continue
            seen_ids.append(r["source_id"])
            processed_results.append(r)
        return processed_results

    def search(self, what, where):
        try:
            auth_token = self.get_auth_token()
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
                results.append(self.parse_result(result))
            return self.deduplicate_results(results)
        except requests.exceptions.RequestException as err:
            raise RuntimeError(f"pagesjaunes api error: {err}")


def search(what, where):
    client = Client()
    return client.search(what, where)
