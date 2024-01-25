import copy
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timedelta
from urllib.parse import urlencode
from uuid import uuid4

import reversion
from django.conf import settings
from django.core.management.base import BaseCommand
from rest_framework.exceptions import ValidationError
from scrapfly import ScrapeConfig, ScrapflyClient, ScrapflyScrapeError

from erp.imports.serializers import ErpImportSerializer
from erp.models import Erp
from erp.provider import geocoder

# NOTE: mainly based on https://github.com/scrapfly/scrapfly-scrapers/blob/main/bookingcom-scraper/bookingcom.py


XPATH_CSS_SELECTORS_DETAIL = {
    "hotel_box": '//div[@data-testid="property-section--content"]/div[2]/div',
    "hotel_type": './/span[contains(@data-testid, "facility-group-icon")]/../text()',
    "hotel_name": "h2.pp-header__title::text",
    "hotel_address": ".hp_address_subtitle::text",
}

XPATH_CSS_SELECTORS_LIST = {
    "hotel_box": '//div[@data-testid="property-card"]',
    "hotel_url": './/h3/a[@data-testid="title-link"]/@href',
    "hotel_name": './/h3/a[@data-testid="title-link"]/div/text()',
}


class Command(BaseCommand):
    help = "Create ERPs using scrapfly"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Connection": "keep-alive",
        "Accept-Language": "fr-FR",
    }

    base_config = {
        # Booking.com requires Anti Scraping Protection bypass feature:
        "asp": True,
        "country": "FR",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--query",
            type=str,
            required=True,
            help="The query you want to search on Outscraper to insert new ERPs",
        )

    def _convert_ext(self, access):
        accessibility = {}

        if "L'établissement ne dispose pas de parking" in access:
            accessibility["stationnement_presence"] = False

        if "Parking intérieur" in access:
            accessibility["stationnement_presence"] = True

        if "Parking accessible aux personnes à mobilité réduite" in access:
            accessibility["stationnement_presence"] = True
            accessibility["stationnement_pmr"] = True

        return accessibility

    def _convert_access(self, access):
        accessibility = {}
        access_copy = copy.deepcopy(access)

        if (key := "Accessible en fauteuil roulant") in access_copy:
            accessibility["entree_plain_pied"] = True
            accessibility["entree_largeur_mini"] = 80
            accessibility["accueil_chambre_nombre_accessibles"] = 1
            access_copy.remove(key)

        if (key := "Logement entièrement accessible en fauteuil roulant") in access_copy:
            accessibility["accueil_chambre_nombre_accessibles"] = 1
            accessibility["entree_plain_pied"] = True
            accessibility["entree_largeur_mini"] = 80
            access_copy.remove(key)

        if (key := "Toilettes avec barres d'appui") in access_copy:
            accessibility["accueil_chambre_sanitaires_barre_appui"] = True
            access_copy.remove(key)

        if (key := "Guidage vocal") in access_copy:
            accessibility["entree_balise_sonore"] = True
            access_copy.remove(key)

        for key_to_ignore in (
            "Logement entièrement situé au rez-de-chaussée",
            "Cordon d'alarme dans la salle de bains",
            "Lavabo bas adapté aux personnes à mobilité réduite",
            "Toilettes surélevées",
            "Aides visuelles : braille",
            "Étages supérieurs accessibles par ascenseur",
            "Étages supérieurs accessibles uniquement par les escaliers",
            "Aides visuelles : panneaux tactiles",
        ):
            if key_to_ignore not in access_copy:
                continue
            access_copy.remove(key_to_ignore)

        # Some access info are allowed only if hotel has accessible bedrooms, but as it depends on the parsing order, wipe it here.
        if accessibility.get("accueil_chambre_nombre_accessibles") != 1:
            accessibility.pop("accueil_chambre_sanitaires_barre_appui", None)

        if access_copy:
            print(f"Extra access keys: {access_copy}")

        if not accessibility:
            return

        accessibility["entree_porte_presence"] = True
        return accessibility

    def _parse_search_page(self, result):
        print(f"parsing search page: {result.context['url']}")
        hotel_previews = []

        for hotel_box in result.selector.xpath(XPATH_CSS_SELECTORS_LIST["hotel_box"]):
            preview = {
                "url": hotel_box.xpath(XPATH_CSS_SELECTORS_LIST["hotel_url"]).get("").split("?")[0],
                "name": hotel_box.xpath(XPATH_CSS_SELECTORS_LIST["hotel_name"]).get(""),
            }
            hotel_previews.append(preview)

        return hotel_previews

    def _parse_hotel(self, result):
        print(f"parsing hotel page: {result.context['url']}")
        sel = result.selector

        features = defaultdict(list)

        for box in sel.xpath(XPATH_CSS_SELECTORS_DETAIL["hotel_box"]):
            type_ = box.xpath(XPATH_CSS_SELECTORS_DETAIL["hotel_type"]).get()
            feats = [f.strip() for f in box.css("li ::text").getall() if f.strip()]
            features[type_] = feats

        css = lambda selector, sep="": sep.join(sel.css(selector).getall()).strip()
        data = {
            "url": result.context["url"],
            "id": re.findall(r"b_hotel_id:\s*'(.+?)'", result.content)[0],
            "title": sel.css(XPATH_CSS_SELECTORS_DETAIL["hotel_name"]).get(),
            "address": css(XPATH_CSS_SELECTORS_DETAIL["hotel_address"]),
            "features": dict(features),
        }
        return data

    def _parse_detail_page(self, hotel):
        if not hotel.get("url"):
            return

        client = ScrapflyClient(key=settings.SCRAPFLY_IO_API_KEY)

        print(f"scraping hotel {hotel['url']}")
        session = str(uuid4()).replace("-", "")
        result = client.scrape(
            ScrapeConfig(
                hotel["url"],
                session=session,
                **self.base_config,
            )
        )
        hotel = self._parse_hotel(result)
        self._create_or_update_erp(hotel)

    def _create_or_update_erp(self, result, existing_erp=None):
        erp = {}

        erp["activite"] = self.activity_name
        erp["source"] = Erp.SOURCE_SCRAPFLY
        erp["source_id"] = result["id"]
        erp["nom"] = result["title"]
        erp["adresse"] = result["address"]

        if not existing_erp:
            print(f"Managing {erp['nom']}, {result['address']}")

        if "Accessibilité" not in result.get("features", {}):
            return

        access = result["features"]["Accessibilité"]
        ext = result["features"]["Parking"]

        erp["accessibilite"] = self._convert_access(access) | self._convert_ext(ext)
        if not erp["accessibilite"]:
            return

        locdata = geocoder.geocode(erp["adresse"])
        for key in ("numero", "voie", "lieu_dit", "code_postal", "commune"):
            erp[key] = locdata.get(key)

        serializer = ErpImportSerializer(data=erp, instance=existing_erp, context={"enrich_only": True})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            if (
                isinstance(e, ValidationError)
                and "non_field_errors" in e.get_codes()
                and "duplicate" in e.get_codes()["non_field_errors"]
            ):
                erp_duplicated = Erp.objects.get(pk=int(e.detail["non_field_errors"][1]))
                return self._create_or_update_erp(result, existing_erp=erp_duplicated)
            return

        action = "UPDATED" if existing_erp else "CREATED"

        try:
            with reversion.create_revision():
                new_erp = serializer.save()
                reversion.set_comment(f"{action} via scrapfly")
        except reversion.errors.RevertError:
            new_erp = serializer.save()

        print(f"{action} ERP available at {new_erp.get_absolute_uri()}")

    def _search(self, query):
        client = ScrapflyClient(key=settings.SCRAPFLY_IO_API_KEY)
        locations = client.scrape(
            ScrapeConfig(
                url="https://accommodations.booking.com/autocomplete.json",
                method="POST",
                headers={
                    "Origin": "https://www.booking.com",
                    "Referer": "https://www.booking.com/",
                    "Content-Type": "text/plain;charset=UTF-8",
                },
                body=f'{{"query":"{query}","pageview_id":"","aid":800210,"language":"fr-fr","size":5}}',
            )
        )
        locations = json.loads(locations.content).get("results")
        if not locations:
            print(f"No location found for {query}")
            return

        now = datetime.now()
        checkin = (now + timedelta(days=60)).strftime("%Y-%m-%d")
        checkout = (now + timedelta(days=61)).strftime("%Y-%m-%d")

        destination = locations[0]
        search_url = "https://www.booking.com/searchresults.fr-fr.html?" + urlencode(
            {
                "ss": destination["value"],
                "ssne": destination["value"],
                "ssne_untouched": destination["value"],
                "checkin": checkin,
                "checkout": checkout,
                "no_rooms": 1,
                "dest_id": destination["dest_id"],
                "dest_type": destination["dest_type"],
                "efdco": 1,
                "group_adults": 1,
                "group_children": 0,
                "lang": "fr-fr",
                "sb": 1,
                "sb_travel_purpose": "leisure",
                "src": "index",
                "src_elem": "sb",
                "nflt": "accessible_facilities%3D185",  # wheelchair accessible
                "flex_window": 7,  # flexible dates: +/-7days
            }
        )

        first_page = client.scrape(ScrapeConfig(search_url, **self.base_config))
        hotel_previews = self._parse_search_page(first_page)

        # parse total amount of pages from heading1 text, e.g: "Paris : 1232 établissements trouvés"
        found = first_page.selector.css("h1").re(r"([\d,]+) établissement[s]? trouvé[s]?")
        if not found:
            return hotel_previews

        _total_results = int(found[0].replace(",", ""))
        _page_size = 25
        total_pages = math.ceil(_total_results / _page_size)
        print(f"scraped {len(hotel_previews)} from 1st result page. {total_pages} to go")

        to_scraps = [
            ScrapeConfig(search_url.replace("offset=0", f"offset={page * _page_size}"), **self.base_config)
            for page in range(2, total_pages + 1)
        ]
        for to_scrap in to_scraps:
            result = client.scrape(to_scrap)
            if not isinstance(result, ScrapflyScrapeError):
                hotel_previews.extend(self._parse_search_page(result))
            else:
                print(f"failed to scrape {result.api_response.config['url']}, got: {result.message}")
            print(f"scraped {len(hotel_previews)} total hotel previews for {query} {checkin}-{checkout}")
        return hotel_previews

    def handle(self, *args, **options):
        self.activity_name = "Hôtel"

        hotels = self._search(query=options["query"])
        for hotel in hotels:
            self._parse_detail_page(hotel)
