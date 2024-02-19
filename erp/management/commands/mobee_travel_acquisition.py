import requests
import reversion
from django.conf import settings
from django.core.management.base import BaseCommand
from rest_framework.exceptions import ValidationError

from erp.imports.serializers import ErpImportSerializer
from erp.models import Erp
from erp.provider import geocoder


class Command(BaseCommand):
    help = "Create ERPs from mobee travel"
    limit_per_page = 10 if settings.DEBUG else 100

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Connection": "keep-alive",
        "Accept-Language": "fr-FR",
    }

    mapping = {
        "Salle de bain accessible aux personnes à mobilité réduite": {"accueil_chambre_douche_plain_pied": True},
        "Douche accessible en fauteuil roulant": {"accueil_chambre_douche_plain_pied": True},
        "Accessibilité de la chambre aux personnes à mobilité réduite": {"accueil_chambre_nombre_accessibles": 1},
        "Barre d'appui près des toilettes": {"accueil_chambre_sanitaires_barre_appui": True},
        "Réception accessible aux personnes en fauteuil roulant": {
            "accueil_cheminement_plain_pied": True,
            "accueil_retrecissement": False,
        },
        "Toilettes publiques accessibles aux personnes en fauteuil roulant": {
            "sanitaires_presence": True,
            "sanitaires_adaptes_presence": True,
        },
        "Parking sans voiturier (en supplément)": {"stationnement_presence": True},
        "Parking accessible aux personnes en fauteuil roulant": {
            "stationnement_presence": True,
            "stationnement_pmr": True,
        },
        "Parking pour vans accessible aux personnes en fauteuil roulant": {
            "stationnement_presence": True,
            "stationnement_pmr": True,
        },
        "Accessible aux personnes en fauteuil roulant (des restrictions peuvent s'appliquer)": {
            "entree_plain_pied": True,
            "entree_largeur_mini": 80,
            "accueil_chambre_nombre_accessibles": 1,
        },
        "Parking sur place": {"stationnement_presence": True},
        "Chaise de douche sur place": {"accueil_chambre_douche_siege": True},
    }

    ignored_infos = [
        "Anglais",
        "Accessible aux personnes en fauteuil roulant",
        "Visuel",
        "Fauteuil élévateur piscine (PMR)",
        "Réception ouverte 24 h/24",
        "Piscine adaptée grâce à un système de mise à l'eau",
        "Label Tourisme & Handicap",
        "Espagnol",
        "Lit médicalisé accepté",
        "Piscine couverte",
        "Espaces fumeurs prévus",
        "Piscine pour enfants",
        "Rampe d'ascenseur accessible aux personnes en fauteuil roulant",
        "Services de concierge",
        "Service de petit-déjeuner",
        "Piscine extérieure",
        "Club pour enfants (gratuit)",
        "Établissement non-fumeurs",
        "Lève personne accepté",
        "Meuble de salle de bain adapté aux personnes en fauteuil roulant",
        "Salle de bain privée",
        "Français",
        "Fauteuils roulants disponibles sur place",
        "Barre d'appui dans la douche",
        "Climatisation",
        "Cuisine adaptée PMR",
        "Piscine accessible aux personnes en fauteuil roulant",
        "Accès Wi-Fi gratuit",
        "Spa accessible aux personnes en fauteuil roulant",
        "Coffre-fort dans la chambre (adapté aux ordinateurs portables)",
        "Salon accessible aux personnes en fauteuil roulant",
        "Rail de transfert piscine - adapté PMR",
        "Promenades en calèche adaptées",
        "Conciergerie accessible aux personnes en fauteuil roulant",
        "Restaurant sur place accessible aux personnes en fauteuil roulant",
        "Allemand",
        "Centre de fitness accessible aux personnes en fauteuil roulant",
        "Fauteuil de mise à l'eau",
        "Consigne à bagages",
        "Ascenseur",
        "Laverie",
        "Auditif",
        "Portes adaptées aux fauteuils roulants",
        "Location de VTT, VTC, VAE, vélos PMR",
        "Service de ménage quotidien",
        "Animaux de compagnie acceptés (gratuitement)",
        "Rampe d'accès pour personnes en fauteuil roulant",
        "Mental",
        "L'établissement confirme qu'il a renforcé ses mesures de nettoyage.",
        "Moteur",
        "Chauffage",
        "Baignoire accessible aux personnes à mobilité réduite",
        "Télévision",
    ]

    def _search(self, page=1):
        results = []
        url = (
            'https://api.mobeetravel.com/items/properties?fields[]=*&meta=*&page=%(page)s&sort[]=-bees&limit=%(limit)s&filter={"_and":[{"coordinates":{"_intersects":{"type":"Feature","bbox":[-6.226902145630049,38.65702481224616,10.597540303969538,53.6515069404918],"properties":{},"geometry":{"type":"Polygon","coordinates":[[[-6.226902145630049,38.65702481224616],[10.597540303969538,38.65702481224616],[10.597540303969538,53.6515069404918],[-6.226902145630049,53.6515069404918],[-6.226902145630049,38.65702481224616]]]}}}},{"bees":{"_in":[3,4,1,2]}},{},{}]}'
            % {"page": page, "limit": self.limit_per_page}
        )
        print(f"Fetching list page n°{page}")
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            print("Non 200 response, exiting...")
            return

        data = response.json()["data"]

        for entry in data:
            if entry["country"] != "France":
                continue

            results.append(entry["slug"])

        if len(data) < self.limit_per_page:
            return results

        page += 1

        if settings.DEBUG:
            if page > 1:
                return results

        results.extend(self._search(page))

        return results

    def _parse_detail_page(self, slug):
        print(f"Managing {slug}")
        url = f"https://www.mobeetravel.com/_next/data/V1Vr1VgJ9kcr_FE4CjsZD/fr/property/{slug}.json"

        response = requests.get(url, headers={"Accept": "application/json"})

        if response.status_code != 200:
            print("Non 200 response, skipping this ERP...")
            return

        self._create_or_update_erp(response.json())

    def _create_or_update_erp(self, result, existing_erp=None):
        result = (result or {}).get("pageProps", {}).get("property")
        if not result:
            return

        erp = {}

        erp["activite"] = self.activity_name
        erp["source"] = Erp.SOURCE_MOBEE_TRAVEL
        erp["source_id"] = result["id"]
        erp["nom"] = result["name"]
        erp["commune"] = result["city"]
        if not result.get("rooms"):
            return

        erp["adresse"] = result["rooms"][0]["property"]["address"]
        erp["adresse"] = f"{erp['adresse']}, {erp['commune']}"
        erp["code_postal"] = result["rooms"][0]["property"]["postal_code"]

        if not existing_erp:
            print(f"Managing {erp['nom']}, {erp['adresse']} {erp['code_postal']} {erp['commune']}")

        if "amenities" not in result:
            return

        erp["accessibilite"] = self._convert_access(result["amenities"])
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
                reversion.set_comment(f"{action} from mobee travel")
        except reversion.errors.RevertError:
            new_erp = serializer.save()

        print(f"{action} ERP available at {new_erp.get_absolute_uri()}")

    def _convert_access(self, access_infos):
        accessibility = {}
        for access in access_infos:
            if access.get("is_accessible") is not True:
                continue

            access["name"] = access["name"].replace("’", "'").strip()
            if access["name"] in self.ignored_infos:
                continue

            access_acceslibre = self.mapping.get(access["name"])
            if not access_acceslibre:
                print(f"{access['name']} not mapped")
                continue

            accessibility |= access_acceslibre

        return accessibility

    def handle(self, *args, **options):
        self.activity_name = "Hôtel"

        slugs = self._search()
        for slug in slugs:
            self._parse_detail_page(slug)
