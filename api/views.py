from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as translate
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import BaseFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework_gis.pagination import GeoJsonPagination

from api.filters import EquipmentFilter, ErpFilter, ZoneFilter
from api.serializers import (
    AccessibiliteSerializer,
    ActiviteWithCountSerializer,
    ErpGeoSerializer,
    ErpSerializer,
    WidgetSerializer,
)
from erp import schema
from erp.imports.serializers import ErpImportSerializer
from erp.models import Accessibilite, Activite, Erp

# Useful docs
# - permissions: https://www.django-rest-framework.org/api-guide/permissions/#api-reference
# - queryable slugs: https://stackoverflow.com/a/32209005/330911
# - pagination style: https://www.django-rest-framework.org/api-guide/pagination/#modifying-the-pagination-style
# - detail view queryset overriding: https://github.com/encode/django-rest-framework/blob/0407a0df8a16fdac94bbd08d49143a74a88001cd/rest_framework/generics.py#L75-L101
# - query string parameters api documentation: https://github.com/encode/django-rest-framework/issues/6992#issuecomment-541711632
# - documenting your views: https://www.django-rest-framework.org/coreapi/from-documenting-your-api/#documenting-your-views
API_DOC_SUMMARY = translate("""
%(site_title)s expose une [API](https://fr.wikipedia.org/wiki/API) publique
permettant d’interroger sa base de données de manière programmatique. Cette API
adopte autant que possible le
[paradigme REST](https://en.wikipedia.org/wiki/Representational_state_transfer) et
expose les résultats aux formats
[JSON](https://en.wikipedia.org/wiki/JavaScript_Object_Notation) ou
[geoJSON](https://en.wikipedia.org/wiki/GeoJSON).

Le point d’entrée racine de l’API est accessible à l’adresse
[`%(site_root_url)s/api/`](%(site_root_url)s/api/) :
- Une vue HTML est présentée lorsqu’elle est demandée depuis un navigateur web ;
- Une réponse de type `application/json` est retournée par défaut ;
- Une réponse de type `application/geo+json` est retournée si elle est explicitement demandée par le client et si elle est disponible.

## Identification

Si vous souhaitez utiliser notre API, nous pouvons vous fournir une clé, à joindre à chaque requête adressée à l’API via l’en-tête HTTP suivant :
```
Authorization: Api-Key <YOUR_API_KEY>
```

Pour demander votre clé d’API, [contactez-nous](%(site_root_url)s/contact/api_key), nous n’avons aucune raison de refuser :-)
Si vous prévoyez d’effectuer des insertions et/ou des mises à jour pendant vos développements, nous recommandons fortement d’utiliser notre plateforme `recette` (clé d’API dédiée).

## Limitation

Afin de garantir la disponibilité de l’API pour tous, un nombre maximal de requêtes par seconde est défini.
Si vous atteignez cette limite, une réponse `HTTP 429 (Too many requests)` sera retournée, vous invitant à réduire la fréquence et le nombre de vos requêtes.

## Règles métier

- Il est uniquement possible de modifier les données d’accessibilité d’un ERP via l’API ; les informations générales de l’ERP ne peuvent pas être modifiées.
- Il est uniquement possible d’enrichir les données ; il n’est pas possible de supprimer des données (un élément ayant une valeur `true` ou `false` ne peut pas passer à `null`).

## Quelques exemples d’utilisation

### Rechercher des établissements dont le nom contient ou est proche de `piscine`, à Villeurbanne :

```
$ curl -X GET %(site_root_url)s/api/erps/?q=piscine&commune=Villeurbanne -H "Authorization: Api-Key <YOUR_API_KEY>"
```

Notez que chaque résultat expose une clé `url`, qui correspond au point d’accès permettant de récupérer la page de détail de l’établissement.
Cette URL peut également être construite dynamiquement à partir de l’UUID de l’établissement : `%(site_root_url)s/uuid/<establishment_uuid>/`

### Rechercher des établissements contenus dans une emprise rectangulaire englobant Valence (France) et les récupérer au format geoJSON afin de les afficher sur une carte :

```
$ curl -X GET %(site_root_url)s/api/erps/?zone=4.849022,44.885530,4.982661,44.963994 -H "accept: application/geo+json" -H "Authorization: Api-Key <YOUR_API_KEY>"
```

Notez que la zone est définie par 2 coordonnées :
- longitude minimale, latitude minimale ;
- longitude maximale, latitude maximale.

Notez également que vous pouvez combiner les filtres (`code_postal`, `q`, `commune`, …) avec la recherche géospatiale décrite ici.

---

### Récupérer les détails d’un établissement donné

```
$ curl -X GET %(site_root_url)s/api/erps/piscine-des-gratte-ciel-2/ -H "Authorization: Api-Key <YOUR_API_KEY>"
```

Notez la présence de la clé `accessibility`, qui expose l’URL du point d’accès permettant de récupérer les données d’accessibilité de cet établissement.

---

### Récupérer les détails d’accessibilité de cet ERP

```
$ curl -X GET %(site_root_url)s/api/accessibility/<OBJECT_ID>/ -H "Authorization: Api-Key <YOUR_API_KEY>"
```
---

### Récupérer les détails d’accessibilité de cet ERP dans un format lisible et accessible

```
$ curl -X GET %(site_root_url)s/api/accessibility/<OBJECT_ID>/?readable=true -H "Authorization: Api-Key <YOUR_API_KEY>"
```
---

### Modifier les données d’accessibilité d’un ERP

```
$ curl -X PATCH %(site_root_url)s/api/erps/<SLUG_DE_L_ERP>/ -H 'Content-Type: application/json' -H 'Authorization: Api-Key <YOUR_API_KEY>' -d '{{"accessibility" : {{"transport_station_presence": "true"}}}}'
```
---

### Récupérer les phrases du widget ERP

```
$ curl -X GET %(site_root_url)s/api/erps/<SLUG_DE_L_ERP>/widget/ -H "Authorization: Api-Key <YOUR_API_KEY>"
```
---

Vous trouverez ci-dessous la documentation technique exhaustive des points d’entrée exposés par l’API.
""") % {"site_root_url": settings.SITE_ROOT_URL, "site_title": settings.SITE_NAME.title()}


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
                "description": "Discard null or non filled values",
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
                "description": "Render a human readable version of accessibility data",
                "schema": {"type": "boolean"},
            },
        },
    }


class AccessibilitePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 1000


class AccessibiliteViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    list:
    This endpoint lists the establishments' **accessibility data**.

    retrieve:
    This endpoint allows to retrieve accessibility data of a given establishment, identified by its ID.
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
                "description": "Municipality name (ex. *Clichy*)",
                "schema": {"type": "string"},
            },
        },
    }


class ActiviteViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    list:
    This endpoint lists the **establishments activities**. It supports following filters:

    - `?commune=Lyon` lists activities of all establishments in the city of *Lyon*

    retrieve:
    This endpoint is here to retrieve info about a given **establishment activity**,
    identified by its [URL slug](https://en.wikipedia.org/wiki/Slug_(publishing))
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


class ErpSchema(A4aAutoSchema):
    query_string_params = {
        "q": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "q",
                "in": "query",
                "required": False,
                "description": "Search query",
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
                "description": "Municipality name (ex. *Clichy*)",
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
                "description": "Municipality postal code (ex. *92120*)",
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
                "description": "Municipality INSEE code (ex. *59359*)",
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
                "description": "Activity slug",
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
                "description": "Establishment SIRET number",
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
                "description": "Name of the third partner",
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
                "description": "Unique ID provided by a third partner",
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
                "description": "Unique ASP ID provided by Service Public",
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
                "description": "A true value will return only establishment having an ASP ID",
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
                "description": "Unique OpenData identifier",
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
                "description": "Geo area, following format `latitude,longitude` (for ex. `?around=45.76,4.83`)",
                "schema": {"type": "string"},
            },
        },
        "ban_id": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "ban_id",
                "in": "query",
                "required": False,
                "description": "BAN address identifier",
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
                "description": "A true value will drop null or non filled accessibilities values.",
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
                "description": "A true value will render a human readable version of accessibilities data.",
                "schema": {"type": "boolean"},
            },
        },
        "with_drafts": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "with_drafts",
                "in": "query",
                "required": False,
                "description": "A true value will also return establishments which are in a draft state (non published).",
                "schema": {"type": "boolean"},
            },
        },
        "created_or_updated_in_last_days": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "created_or_updated_in_last_days",
                "in": "query",
                "required": False,
                "description": "Filter establishments which have been created or updated during the last X days.",
                "schema": {"type": "integer"},
            },
        },
    }


class ErpViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    list:
    This endpoint lists the establishments (ERPs). It supports the following filters:

    - `?q=impôts` search the establishments containing the *impôts* term in their name or activity
    - `?commune=Lyon` returns establishments in *Lyon* city
    - `?activite=administration-publique` returns the establishments having *Administration publique* as activity
    - `?q=impôts&commune=Lyon&activite=administration-publique` returns *administrations publiques* establishments containing
      *impôts* term and located in the city of *Lyon*. You can also filter by city to have more precise results, by using `code_postal` or `code_insee` fields.
    - `?source=gendarmerie&source_id=1002326` returns a record identified by its `source` and `source_id`.
    - `?source=sp&asp_id=00033429-1b83-46b4-9101-3a2ad178af79` allows to search for an establishment by its Service Public ID (ASP_ID).
    - `?uuid=d8823070-f999-4992-92e9-688be87a76a6` allows to search for an establishment idendified by its [unique OpenData identifier](https://schema.data.gouv.fr/MTES-MCT/acceslibre-schema/latest/documentation.html#propri%C3%A9t%C3%A9-id).

    retrieve:
    This endpoint returns data for a given establishment identified by its [slug](https://en.wikipedia.org/wiki/Slug_(publishing))
    (*slug*).

    create:
    This endpoint is used to create an establishment, for an existing activity, identified by its [slug](https://en.wikipedia.org/wiki/Slug_(publishing))
    (*slug*) having accessibility data.

    update:
    This endpoint is used to partially update accessibility data of a given establishment, identified by its [slug](https://en.wikipedia.org/wiki/Slug_(publishing)).
    """

    serializers = {
        "default": ErpSerializer,
        "list": ErpSerializer,
        "create": ErpImportSerializer,
        "partial_update": ErpImportSerializer,
    }

    queryset = Erp.objects.select_related("activite", "accessibilite").order_by("nom")
    lookup_field = "slug"
    bbox_filter_field = "geom"
    filter_backends = (ZoneFilter, EquipmentFilter, ErpFilter)
    schema = ErpSchema()
    http_method_names = ["get", "post", "patch"]

    def get_serializer_class(self):
        if self.request and self.request.headers.get("Accept") == "application/geo+json":
            return ErpGeoSerializer
        return self.serializers.get(self.action, self.serializers["default"])

    def get_pagination_class(self):
        if self.request and self.request.headers.get("Accept") == "application/geo+json":
            return GeoJsonPagination
        return ErpPagination

    pagination_class = property(fget=get_pagination_class)

    @action(methods=["get"], detail=True, url_path="widget", url_name="widget")
    def get_widget(self, request, slug=None):
        erp = get_object_or_404(self.filter_queryset(self.get_queryset()), slug=slug)
        serializer = WidgetSerializer(erp)
        return Response(serializer.data)
