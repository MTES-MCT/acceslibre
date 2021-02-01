import logging
import requests
import time

from django.conf import settings

from core.lib import text
from erp.models import Commune


logger = logging.getLogger(__name__)

BASE_URL = "https://api.pagesjaunes.fr"

client = None

# PAGESJAUNES_API_AUTH_TTL
# PAGESJAUNES_API_CLIENT_KEY
# PAGESJAUNES_API_SECRET_KEY
# PAGESJAUNES_API_AUTH_TOKEN
# PAGESJAUNES_API_LAST_FETCHED


class Client:
    """PageJaunes (SoLocal) API client.

    @see https://developer.pagesjaunes.fr/quickstart#quickstart
    """

    auth_token = None
    auth_token_last_fetched = None

    def __init__(self):
        self.client_id = settings.PAGESJAUNES_API_CLIENT_KEY
        self.client_secret = settings.PAGESJAUNES_API_SECRET_KEY
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Client needs client auth credentials")
        self.auth_token = settings.PAGESJAUNES_API_AUTH_TOKEN
        self.auth_token_last_fetched = settings.PAGESJAUNES_API_LAST_FETCHED

    def get_auth_token(self, now=None):
        # If we have a valid token in memory, return it
        now = now or time.time()
        if (
            self.auth_token
            and self.auth_token_last_fetched
            and now - self.auth_token_last_fetched < settings.PAGESJAUNES_API_AUTH_TTL
        ):
            logger.info("reusing pagejaunes auth token")
            return self.auth_token
        # Request auth token
        logger.info("fetching new pagejaunes auth token")
        try:
            res = requests.post(
                f"{BASE_URL}/oauth/client_credential/accesstoken",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            self.auth_token_last_fetched = (
                settings.PAGESJAUNES_API_LAST_FETCHED
            ) = time.time()
            self.auth_token = settings.PAGESJAUNES_API_AUTH_TOKEN = res.json()[
                "access_token"
            ]
            return self.auth_token
        except requests.exceptions.RequestException as err:
            raise RuntimeError(f"pagesjaunes api error: {err}")

    def parse_result(self, result):
        # place infos
        infos = result["inscriptions"][0]
        nom = result.get("merchant_name")
        (numero, voie) = text.extract_numero_voie(infos.get("address_street"))
        address_city = infos.get("address_city")
        code_postal = infos.get("address_zipcode")
        commune_ext = Commune.objects.search_by_nom_code_postal(
            address_city, code_postal
        ).first()
        if commune_ext:
            commune = commune_ext.nom
            code_insee = commune_ext.code_insee
        else:
            commune = address_city
            code_insee = None
        # photos
        photos = [p["url"] for p in result.get("visual_urls", [])]
        photo = photos[0] if len(photos) > 0 else None

        return dict(
            actif=True,
            source="pagesjaunes",
            source_id=result.get("merchant_id"),
            nom=nom,
            numero=numero,
            voie=voie,
            code_postal=code_postal,
            commune=commune,
            code_insee=code_insee,
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
            logger.info(f"pagesjaunes api call: {res.url}")
            json = res.json()
            results = []
            for result in json["search_results"]["listings"]:
                results.append(self.parse_result(result))
            return self.deduplicate_results(results)
        except requests.exceptions.RequestException as err:
            raise RuntimeError(f"pagesjaunes api error: {err}")


def query(what, where):
    return Client().search(what, where)


def search(what, where):
    try:
        return query(what, where)
    except RuntimeError as err:
        logger.error(err)
        return []
