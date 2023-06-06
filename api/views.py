from django.conf import settings
from django.contrib.gis.geos import Point
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import BaseFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework_gis.filters import InBBoxFilter
from rest_framework_gis.pagination import GeoJsonPagination

from api.serializers import AccessibiliteSerializer, ActiviteWithCountSerializer, ErpGeoSerializer, ErpSerializer
from erp import schema
from erp.models import Accessibilite, Activite, Erp
from erp.provider import geocoder

# Useful docs
# - permissions: https://www.django-rest-framework.org/api-guide/permissions/#api-reference
# - queryable slugs: https://stackoverflow.com/a/32209005/330911
# - pagination style: https://www.django-rest-framework.org/api-guide/pagination/#modifying-the-pagination-style
# - detail view queryset overriding: https://github.com/encode/django-rest-framework/blob/0407a0df8a16fdac94bbd08d49143a74a88001cd/rest_framework/generics.py#L75-L101
# - query string parameters api documentation: https://github.com/encode/django-rest-framework/issues/6992#issuecomment-541711632
# - documenting your views: https://www.django-rest-framework.org/coreapi/from-documenting-your-api/#documenting-your-views

API_DOC_SUMMARY = f"""
{settings.SITE_NAME.title()} expose une [API](https://fr.wikipedia.org/wiki/Interface_de_programmation)
publique permettant d'interroger programmatiquement sa base de données. Cette API embrasse le paradigme
[REST](https://fr.wikipedia.org/wiki/Representational_state_transfer) autant que possible et
expose les résultats au format [JSON](https://fr.wikipedia.org/wiki/JavaScript_Object_Notation) ou [geoJSON](https://fr.wikipedia.org/wiki/GeoJSON).

Le point d'entrée racine de l'API est accessible à l'adresse
[`{settings.SITE_ROOT_URL}/api/`]({settings.SITE_ROOT_URL}/api/):
- Une vue HTML est présentée quand requêtée par le biais d'un navigateur Web,
- Une réponse de type `application/json` est restituée par défaut.
- Une réponse de type `application/geo+json` est restituée si explicitement demandée par le client et si disponible.

## Identification

Si vous voulez utiliser notre API, nous pouvons vous fournir une clef, à joindre à chaque requête à l'API via l'entête suivante :
```
Authorization: Api-Key <VOTRE_CLEF_API>
```

Pour demander votre clef API, [contactez-nous]({settings.SITE_ROOT_URL}/contact/api_key), nous n'avons, à priori, pas de raison de refuser :-)

## Limitation

Afin de garantir la disponibilité du site pour tous, un nombre maximum de requêtes par seconde est défini.
Si vous atteignez cette limite, une réponse `HTTP 429 (Too many requests)` sera émise, vous invitant à réduire la fréquence de vos requêtes.

## Quelques exemples d'utilisation

### Rechercher les établissements dont le nom contient ou s'approche de `piscine`, à Villeurbanne :

```
$ curl -X GET {settings.SITE_ROOT_URL}/api/erps/?q=piscine&commune=Villeurbanne -H "Authorization: Api-Key <VOTRE_CLEF_API>"
```

Notez que chaque résultat expose une clé `url`, qui est un point de récupération des informations de l'établissement.


### Rechercher les établissements contenu dans un cadre englobant Valence et les récupérer au format geoJSON en vue de les afficher sur une carte :

```
$ curl -X GET {settings.SITE_ROOT_URL}/api/erps/?in_bbox=4.849022,44.885530,4.982661,44.963994 -H "accept: application/geo+json" -H "Authorization: Api-Key <VOTRE_CLEF_API>"
```

Notez que le cadre est définit par 2 coordonnées :
- min longitude, min latitude
- max longitude, max latitude

Notez également que vous pouvez combiner les filtres (`code_postal`, `q`, `commune`, ...) et la recherche geospatiale décrite ici.

---

### Récupérer les détails d'un établissement particulier

```
$ curl -X GET {settings.SITE_ROOT_URL}/api/erps/piscine-des-gratte-ciel-2/ -H "Authorization: Api-Key <VOTRE_CLEF_API>"
```

Notez la présence de la clé `accessibilite` qui expose l'URL du point de récupération des données d'accessibilité pour cet établissement.

---

### Récupérer les détails d'accessibilité pour cet ERP

```
$ curl -X GET {settings.SITE_ROOT_URL}/api/accessibilite/80/ -H "Authorization: Api-Key <VOTRE_CLEF_API>"
```

---

### Récupérer les détails d'accessibilité pour cet ERP en format lisible et accessible

```
$ curl -X GET {settings.SITE_ROOT_URL}/api/accessibilite/80/?readable=true -H "Authorization: Api-Key <VOTRE_CLEF_API>"
```

---

Vous trouverez ci-après la documentation technique exhaustives des points d'entrée exposés par l'API.
"""


class A4aAutoSchema(AutoSchema):
    """A custom DRF schema allowing to define documentation for query string parameters.

    see: https://github.com/encode/django-rest-framework/issues/6992#issuecomment-541711632
    """

    def get_operation(self, path, method):
        op = super().get_operation(path, method)
        for _, rule in self.query_string_params.items():
            if path in rule["paths"] and method in rule["methods"]:
                op["parameters"].append(rule["field"])
        return op


class AccessibiliteFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset


class AccessibiliteSchema(A4aAutoSchema):
    query_string_params = {
        "clean": {
            "paths": ["/accessibilite/"],
            "methods": ["GET"],
            "field": {
                "name": "clean",
                "in": "query",
                "required": False,
                "description": "Écarter les valeurs nulles ou non-renseignées",
                "schema": {"type": "boolean"},
            },
        },
        "readable": {
            "paths": ["/accessibilite/"],
            "methods": ["GET"],
            "field": {
                "name": "readable",
                "in": "query",
                "required": False,
                "description": "Formater les données d'accessibilité pour une lecture humaine",
                "schema": {"type": "boolean"},
            },
        },
    }


class AccessibilitePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 1000


class AccessibiliteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Ce point d'accès liste les **critères d'accessibilité** des ERP.

    retrieve:
    Ce point d'accès permet de récupérer les informations d'accessibilité d'un ERP
    spécifique, à partir de son identifiant.

    **L'obtention de cette URL s'obtient en interrogeant la propriété `accessibilite`
    d'un objet *Erp*.**
    """

    queryset = Accessibilite.objects.select_related("erp").filter(erp__published=True).order_by("-updated_at")
    serializer_class = AccessibiliteSerializer
    pagination_class = AccessibilitePagination
    filter_backends = [AccessibiliteFilterBackend]
    schema = AccessibiliteSchema()

    @action(detail=False, methods=["get"])
    def help(self, request, pk=None):
        """Documente les différents champs d'accessibilité, spécifiant pour chacun :
        - Le libellé du champ
        - La documentation du champ
        """
        repr = {}
        for _, data in schema.get_api_fieldsets().items():
            for field in data["fields"]:
                repr[field] = {
                    "label": schema.get_label(field),
                    "help": schema.get_help_text(field),
                }
        return Response(repr)


class ActivitePagination(PageNumberPagination):
    page_size = 300


class ActiviteFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        # Commune (legacy)
        commune = request.query_params.get("commune", None)
        if commune is not None:
            queryset = queryset.filter(erp__commune_ext__nom__unaccent__iexact=commune)

        return queryset.with_erp_counts()


class ActiviteSchema(A4aAutoSchema):
    query_string_params = {
        "commune": {
            "paths": ["/activites/"],
            "methods": ["GET"],
            "field": {
                "name": "commune",
                "in": "query",
                "required": False,
                "description": "Nom de la commune (ex. *Clichy*)",
                "schema": {"type": "string"},
            },
        },
    }


class ActiviteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Ce point d'accès liste les **activités d'ERP**. Il accepte les filtres suivants :

    - `?commune=Lyon` remonte la liste des activités de l'ensemble des ERP de la ville de *Lyon*

    retrieve:
    Ce point d'accès permet de récupérer les informations liées à une **activité d'ERP**
    spécifique, identifiée par son [identifiant d'URL](https://fr.wikipedia.org/wiki/Slug_(journalisme))
    (*slug*).
    """

    queryset = Activite.objects.order_by("nom")
    serializer_class = ActiviteWithCountSerializer
    lookup_field = "slug"
    pagination_class = ActivitePagination
    filter_backends = [ActiviteFilterBackend]
    schema = ActiviteSchema()


class ErpPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "page_size": self.get_page_size(self.request),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )


class ErpFilterBackend(BaseFilterBackend):
    # FIXME: do NOT apply filters on details view
    def filter_queryset(self, request, queryset, view):
        use_distinct = False
        # Commune (legacy)
        commune = request.query_params.get("commune", None)
        if commune is not None:
            queryset = queryset.filter(commune__unaccent__icontains=commune)

        # Code postal
        code_postal = request.query_params.get("code_postal", None)
        if code_postal is not None:
            queryset = queryset.filter(code_postal=code_postal)

        # Code INSEE
        code_insee = request.query_params.get("code_insee", None)
        if code_insee is not None:
            queryset = queryset.filter(commune_ext__code_insee=code_insee)

        # Activité
        activite = request.query_params.get("activite", None)
        if activite is not None:
            queryset = queryset.having_activite(activite)

        # SIRET
        siret = request.query_params.get("siret", None)
        if siret is not None:
            queryset = queryset.filter(siret=siret)

        # Search
        search_terms = request.query_params.get("q", None)
        if search_terms is not None:
            use_distinct = False
            queryset = queryset.search_what(search_terms)

        # Source Externe
        source = request.query_params.get("source", None)
        if source is not None:
            queryset = queryset.filter(source__iexact=source)

        # Id Externe
        source_id = request.query_params.get("source_id", None)
        if source_id is not None:
            queryset = queryset.filter(source_id__iexact=source_id)

        # ASP Id
        asp_id = request.query_params.get("asp_id", None)
        if asp_id is not None:
            queryset = queryset.filter(asp_id__iexact=asp_id)

        # ASP ID is not null
        asp_id_not_null = request.query_params.get("asp_id_not_null", None)
        if asp_id_not_null is not None:
            if asp_id_not_null == "true":
                queryset = queryset.exclude(asp_id__isnull=True).exclude(asp_id__exact="")
            else:
                queryset = queryset.filter(asp_id__isnull=True)

        # UUID
        uuid = request.query_params.get("uuid", None)
        if uuid is not None:
            queryset = queryset.filter(uuid=uuid)

        # Proximity
        around = geocoder.parse_coords(request.query_params.get("around"))
        if around is not None:
            lat, lon = around
            queryset = queryset.nearest(Point(lon, lat, srid=4326))
            use_distinct = False

        if use_distinct:
            queryset = queryset.distinct("id", "nom")
        return queryset


class ErpSchema(A4aAutoSchema):
    query_string_params = {
        "q": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "q",
                "in": "query",
                "required": False,
                "description": "Termes de recherche",
                "schema": {"type": "string"},
            },
        },
        "commune": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "commune",
                "in": "query",
                "required": False,
                "description": "Nom de la commune (ex. *Clichy*)",
                "schema": {"type": "string"},
            },
        },
        "code_postal": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "code_postal",
                "in": "query",
                "required": False,
                "description": "Code postal de la commune (ex. *92120*)",
                "schema": {"type": "string"},
            },
        },
        "code_insee": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "code_insee",
                "in": "query",
                "required": False,
                "description": "Code INSEE de la commune (ex. *59359*)",
                "schema": {"type": "string"},
            },
        },
        "activite": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "activite",
                "in": "query",
                "required": False,
                "description": "Identifiant d'URL de l'activité (slug)",
                "schema": {"type": "string"},
            },
        },
        "siret": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "siret",
                "in": "query",
                "required": False,
                "description": "Numéro SIRET de l'établissement",
                "schema": {"type": "string"},
            },
        },
        "source": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "source",
                "in": "query",
                "required": False,
                "description": "Nom du fournisseur tier",
                "schema": {"type": "string"},
            },
        },
        "source_id": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "source_id",
                "in": "query",
                "required": False,
                "description": "ID unique fourni par un fournisseur tier",
                "schema": {"type": "string"},
            },
        },
        "asp_id": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "asp_id",
                "in": "query",
                "required": False,
                "description": "ID ASP unique fourni par Service Public",
                "schema": {"type": "string"},
            },
        },
        "asp_id_not_null": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "asp_id_not_null",
                "in": "query",
                "required": False,
                "description": "ID ASP fournit",
                "schema": {"type": "boolean"},
            },
        },
        "uuid": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "uuid",
                "in": "query",
                "required": False,
                "description": "Identifiant unique OpenData",
                "schema": {"type": "string"},
            },
        },
        "around": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "around",
                "in": "query",
                "required": False,
                "description": "Biais de localisation géographique, au format `latitude,longitude` (par ex. `?around=45.76,4.83`)",
                "schema": {"type": "string"},
            },
        },
        "clean": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "clean",
                "in": "query",
                "required": False,
                "description": "Écarter les valeurs nulles ou non-renseignées",
                "schema": {"type": "boolean"},
            },
        },
        "readable": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "readable",
                "in": "query",
                "required": False,
                "description": "Formater les données d'accessibilité pour une lecture humaine",
                "schema": {"type": "boolean"},
            },
        },
    }


class ErpViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Ce point d'accès liste les ERP. Il accepte et permet de combiner plusieurs
    filtres via des paramètres spécifiques :

    - `?q=impôts` recherche les ERP contenant le terme *impôts* dans son nom ou son activité
    - `?commune=Lyon` remonte les ERP de la ville de *Lyon*
    - `?activite=administration-publique` remonte les ERP ayant
      *Administration publique* pour activité
    - `?q=impôts&commune=Lyon&activite=administration-publique` remonte les
      *administrations publiques* contenant le terme *impôts* situés dans la ville
      de *Lyon*. Vous pouvez également filtrer par ville plus précisément en utilisant
      au choix les champs `code_postal` ou `code_insee`.
    - `?source=gendarmerie&source_id=1002326` permet de rechercher un enregistrement
      par source et identifiant dans la source.
    - `?source=sp&asp_id=00033429-1b83-46b4-9101-3a2ad178af79` permet de rechercher un enregistrement
      pour la source Service Public et identifiant ASP de la source.
    - `?uuid=d8823070-f999-4992-92e9-688be87a76a6` permet de rechercher un enregistrement
      par son [identifiant unique OpenData](https://schema.data.gouv.fr/MTES-MCT/acceslibre-schema/latest/documentation.html#propri%C3%A9t%C3%A9-id).

    retrieve:
    Ce point d'accès permet de récupérer les données d'un ERP spécifique, identifié
    par son [identifiant d'URL](https://fr.wikipedia.org/wiki/Slug_(journalisme))
    (*slug*).
    """

    queryset = Erp.objects.select_related("activite", "accessibilite").published().order_by("nom")
    lookup_field = "slug"
    bbox_filter_field = "geom"
    filter_backends = (InBBoxFilter, ErpFilterBackend)
    schema = ErpSchema()

    def get_serializer_class(self):
        if self.request.headers.get("Accept") == "application/geo+json":
            return ErpGeoSerializer
        return ErpSerializer

    def get_pagination_class(self):
        if self.request.headers.get("Accept") == "application/geo+json":
            return GeoJsonPagination
        return ErpPagination

    pagination_class = property(fget=get_pagination_class)
