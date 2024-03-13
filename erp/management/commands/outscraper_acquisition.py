import reversion
from django.conf import settings
from django.core.management.base import BaseCommand
from outscraper import ApiClient
from rest_framework.exceptions import ValidationError

from erp.imports.serializers import ErpImportSerializer
from erp.models import Commune, Erp
from erp.provider.departements import DEPARTEMENTS

QUERIES = [
    ("Boulangerie", "Boulangerie Pâtisserie"),
    ("Pharmacie", "Pharmacie"),
    ("Cimetière", "Cimetière"),
    ("EHPAD", "EHPAD"),
    ("Laboratoire d'analyse médicale", "Laboratoire d'analyse médicale"),
    ("Toilettes publiques", "Toilettes publiques"),
    ("Médiathèque", "Bibliothèque médiathèque"),
    ("Piscine municipale", "Piscine, centre aquatique"),
    ("Boucherie", "Boucherie / commerce de viande"),
    ("Charcuterie", "Boucherie / commerce de viande"),
    ("Bijouterie", "Bijouterie joaillerie"),
    ("Quincaillerie", "Droguerie"),
    ("Librairie", "Librairie"),
    ("Agence immobilière", "Agence immobilière"),
    ("Office du tourisme", "Office du tourisme"),
    ("Kebab", "Restauration rapide"),
    ("Pompes funèbres", "Pompes funèbres"),
    ("Coiffeur", "Coiffure"),
    ("Fleuriste", "Fleuriste"),
    ("Chocolatier", "Chocolatier"),
    ("Coworking", "Coworking"),
    ("Carrosserie", "Carrosserie"),
    ("Vétérinaire", "Vétérinaire"),
    ("Auto-Ecole", "Auto école"),
    ("Centre hospitalier", "Hôpital"),
    ("Esthéticienne", "Soins de beauté, esthétique"),
    ("Stade municipal", "Stade"),
    ("Salle des fêtes", "Salle des fêtes"),
    ("Fromagerie", "Crèmerie Fromagerie"),
    ("Dentiste", "Chirurgien dentiste"),
    ("Lycée", "Collège"),
    ("Collège", "Collège"),
    ("Photographe", "Photographie"),
    ("Opticien", "Opticien"),
]


class Command(BaseCommand):
    help = "Create ERPs from outscraper API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--query",
            type=str,
            required=True,
            help="The query you want to search on Outscraper to insert new ERPs",
        )
        parser.add_argument(
            "--activity",
            type=str,
            required=True,
            help="The name of the Activity, ex: Restaurant",
        )
        parser.add_argument(
            "--skip",
            type=int,
            required=False,
            default=0,
            help="Skip the first X results, mainly here to resume at a given point.",
        )
        parser.add_argument(
            "--max_results",
            type=int,
            required=False,
            default=None,
            help="Limit the number of fetched results, mainly here to control the billing/credits.",
        )

    mapping_acceslibre_outscraper = {
        "nom": "name",
        "site_internet": "site",
        "commune": "city",
        "code_postal": "postal_code",
        "voie": "street",
    }

    def _convert_access(self, access):
        accessibility = {"entree_porte_presence": True}
        if access.get("Entrée accessible en fauteuil roulant") is True:
            accessibility["entree_plain_pied"] = True
            accessibility["entree_largeur_mini"] = 90

        if access.get("Équipé pour les malentendants") is True:
            accessibility["accueil_equipements_malentendants_presence"] = True

        if access.get("Parking accessible en fauteuil roulant") is True:
            accessibility["stationnement_presence"] = True
            accessibility["stationnement_pmr"] = True

        if access.get("Toilettes accessibles en fauteuil roulant") is True:
            accessibility["sanitaires_presence"] = True
            accessibility["sanitaires_adaptes"] = True

        if access.get("Boucle magnétique") is True:
            accessibility["accueil_equipements_malentendants_presence"] = True
            accessibility["accueil_equipements_malentendants"] = ["bim"]

        if access.get("Places assises accessibles en fauteuil roulant") is True:
            accessibility["accueil_chemin_plain_pied"] = True
            accessibility["accueil_retrecissement"] = False

        for key in access:
            if key not in (
                "Places assises accessibles en fauteuil roulant",
                "Entrée accessible en fauteuil roulant",
                "Équipé pour les malentendants",
                "Parking accessible en fauteuil roulant",
                "Toilettes accessibles en fauteuil roulant",
                "Ascenseur accessible en fauteuil roulant",
                "Boucle magnétique",
            ):
                print(f"Extra access key {key}")

        return accessibility

    def _delete_erp(self, existing_erp):
        print(f"Delete permanently closed ERP: {existing_erp}")
        existing_erp.delete()

    def _create_or_update_erp(self, result, existing_erp=None):
        erp = {}

        # NOTE: in case of update, the ERP info won't be updated, only accessibility is updated
        for acceslibre_key, outscraper_key in self.mapping_acceslibre_outscraper.items():
            if outscraper_key not in result:
                # Consider all fields as mandatory
                return None
            erp[acceslibre_key] = result[outscraper_key]

        erp["activite"] = self.activity_name
        erp["source"] = Erp.SOURCE_OUTSCRAPER
        erp["source_id"] = result["place_id"]

        if not existing_erp:
            print(f"Managing {erp['nom']}, {result['street']} {result['postal_code']} {result['city']}")

        if "Accessibilité" not in result.get("about", {}):
            return

        access = result["about"]["Accessibilité"]

        erp["accessibilite"] = self._convert_access(access)

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
                if result["business_status"] == "CLOSED_PERMANENTLY":
                    return self._delete_erp(erp_duplicated)
                return self._create_or_update_erp(result, existing_erp=erp_duplicated)
            return None

        action = "CREATED"
        if existing_erp:
            action = "UPDATED"

        try:
            with reversion.create_revision():
                new_erp = serializer.save()
                reversion.set_comment(f"{action} via outscraper")
        except reversion.errors.RevertError:
            new_erp = serializer.save()

        print(f"{action} ERP available at {new_erp.get_absolute_uri()}")

    def _search(self, query, limit=20, skip=0, max_results=None, total_results=0):
        client = ApiClient(api_key=settings.OUTSCRAPER_API_KEY)
        results = client.google_maps_search(query, limit=limit, skip=skip, language="fr", region="FR")[0]
        print(f"Fetched {limit} results for `{query}`, skipping the first {skip} results")
        for result in results:
            self._create_or_update_erp(result)

        total_results += len(results)

        if max_results is not None and total_results >= max_results:
            return results

        if len(results) < limit:
            return results

        return self._search(query, limit=limit, skip=skip + limit, max_results=max_results, total_results=total_results)

    def handle(self, *args, **options):
        self.activity_name = options["activity"]
        limit = 20

        self._search(query=options["query"], limit=limit, skip=options["skip"], max_results=options["max_results"])


def print_commands():
    for term, activity in QUERIES:
        for num, data in DEPARTEMENTS.items():
            if any([str(num).startswith(x) for x in ["97", "98"]]):
                # ignore DOM, no data for them
                continue
            print(f'python manage.py outscraper_acquisition --query="{term}, {data["nom"]}" --activity="{activity}"')

        for commune in Commune.objects.filter(population__gte=50000):
            if any([str(commune.code_postaux[0]).startswith(x) for x in ["97", "98"]]):
                # ignore DOM, no data for them
                continue
            if "arrondissement" in commune.nom:
                # ignore, will be managed while processing the whole city
                continue
            print(f'python manage.py outscraper_acquisition --query="{term}, {commune.nom}" --activity="{activity}"')
