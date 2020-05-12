from django import forms
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView
from rest_framework.filters import BaseFilterBackend

from erp import geocoder
from erp.models import Accessibilite, Activite, Erp
from erp.schema import get_accessibilite_api_schema
from .serializers import (
    AccessibiliteSerializer,
    ActiviteSerializer,
    ActiviteWithCountSerializer,
    ErpSerializer,
)

# Useful docs
# - permissions: https://www.django-rest-framework.org/api-guide/permissions/#api-reference
# - queryable slugs: https://stackoverflow.com/a/32209005/330911
# - pagination style: https://www.django-rest-framework.org/api-guide/pagination/#modifying-the-pagination-style
# - detail view queryset overriding: https://github.com/encode/django-rest-framework/blob/0407a0df8a16fdac94bbd08d49143a74a88001cd/rest_framework/generics.py#L75-L101
# - query string parameters api documentation: https://github.com/encode/django-rest-framework/issues/6992#issuecomment-541711632
# - documenting your views: https://www.django-rest-framework.org/coreapi/from-documenting-your-api/#documenting-your-views


API_DOC_SUMMARY = """
Access4all expose une [API](https://fr.wikipedia.org/wiki/Interface_de_programmation) publique
permettant d'interroger programmatiquement sa base de données. Cette API embrasse le paradigme
[REST](https://fr.wikipedia.org/wiki/Representational_state_transfer) autant que possible et
expose les résultats au format [JSON](https://fr.wikipedia.org/wiki/JavaScript_Object_Notation).

Le point d'entrée racine de l'API est accessible à l'adresse
[`https://access4all.beta.gouv.fr/api/`](https://access4all.beta.gouv.fr/api/),
et une présentation HTML quand utilisée par biais d'un navigateur Web.

#### Quelques exemples d'utilisation

##### Rechercher les établissements dont le nom contient ou s'approche de `piscine`, à Villeurbanne :

```
$ curl -X GET http://access4all.beta.gouv.fr/api/erps/?q=piscine&commune=Villeurbanne -H "accept: application/json"
```

Notez que chaque résultat expose une clé `url`, qui est un point de récupération des informations de l'établissement.

---

##### Récupérer les détails d'un établissement particulier

```
$ curl -X GET http://access4all.beta.gouv.fr/api/erps/piscine-des-gratte-ciel-2/ -H "accept: application/json"
```

Notez la présence de la clé `accessbilite` qui expose l'URL du point de récupération des données d'accessibilité pour cet établissement.

---

##### Récupérer les détails d'accessibilité pour cet ERP

```
$ curl -X GET http://access4all.beta.gouv.fr/api/accessibilite/80/ -H "accept: application/json"
```

---

Vous trouverez ci-après la documentation technique exhaustives des points d'entrée exposés par l'API.
"""


class A4aAutoSchema(AutoSchema):
    """ A custom DRF schema allowing to define documentation for query string parameters.

        see: https://github.com/encode/django-rest-framework/issues/6992#issuecomment-541711632
    """

    def get_operation(self, path, method):
        op = super().get_operation(path, method)
        for param, rule in self.query_string_params.items():
            if path in rule["paths"] and method in rule["methods"]:
                op["parameters"].append(rule["field"])
        return op


class AccessibilitePagination(PageNumberPagination):
    page_size = 20


class AccessibiliteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Ce point d'accès liste les **critères d'accessibilité** des ERP.

    retrieve:
    Ce point d'accès permet de récupérer les informations d'accessibilité d'un ERP
    spécifique, à partir de son identifiant.

    **L'obtention de cette URL s'obtient en interrogeant la propriété `acessibilite`
    d'un objet *Erp*.**
    """

    queryset = Accessibilite.objects.filter(erp__published=True).order_by("-updated_at")
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = AccessibiliteSerializer
    pagination_class = AccessibilitePagination

    @action(detail=False, methods=["get"])
    def help(self, request, pk=None):
        """ Documente les différents champs d'accessibilité, spécifiant pour chacun :
            - Le libellé du champ
            - La documentation du champ
        """
        repr = {}
        for _, data in get_accessibilite_api_schema().items():
            for field in data["fields"]:
                repr[field] = {
                    "label": getattr(Accessibilite, field).field.verbose_name,
                    "help": getattr(Accessibilite, field).field.help_text,
                }
        return Response(repr)


class ActivitePagination(PageNumberPagination):
    page_size = 300


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
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = ActiviteWithCountSerializer
    lookup_field = "slug"
    pagination_class = ActivitePagination
    schema = ActiviteSchema()

    def get_queryset(self):
        queryset = self.queryset
        commune = self.request.query_params.get("commune")
        if commune is not None:
            queryset = queryset.in_commune(commune)
        return queryset.with_erp_counts()


class ErpPagination(PageNumberPagination):
    page_size = 20


class ErpFilterBackend(BaseFilterBackend):
    # FIXME: do NOT apply filters on details view
    def filter_queryset(self, request, queryset, view):
        # Commune (legacy)
        commune = request.query_params.get("commune", None)
        if commune is not None:
            queryset = queryset.filter(commune__unaccent__icontains=commune)

        # Code postal
        code_postal = request.query_params.get("code_postal", None)
        if code_postal is not None:
            queryset = queryset.filter(
                commune_ext__code_postaux__contains=[code_postal]
            )

        # Code INSEE
        code_insee = request.query_params.get("code_insee", None)
        if code_insee is not None:
            queryset = queryset.filter(commune_ext__code_insee=code_insee)

        # Activité
        activite = request.query_params.get("activite", None)
        if activite is not None:
            queryset = queryset.having_activite(activite)

        # Search
        search_terms = request.query_params.get("q", None)
        if search_terms is not None:
            queryset = queryset.search(search_terms)

        # Proximity
        around = geocoder.parse_coords(request.query_params.get("around"))
        if around is not None:
            queryset = queryset.nearest(around)

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
        "around": {
            "paths": ["/erps/"],
            "methods": ["GET"],
            "field": {
                "name": "around",
                "in": "query",
                "required": False,
                "description": "Biais de localisation géographique, au format `latitude,longitude`",
                "schema": {"type": "string"},
            },
        },
    }


class ErpViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Ce point d'accès liste les ERP. Il accepte et permet de combiner plusieurs
    filtres via des paramètres spécifiques :

    - `?q=impôts` recherche les ERP contenant le terme *impôts* dans son nom,
      son adresse ou son activité
    - `?commune=Lyon` remonte les ERP de la ville de *Lyon*
    - `?activite=administration-publique` remonte les ERP ayant
      *Administration publique* pour activité
    - `?q=impôts&commune=Lyon&activite=administration-publique` remonte les
      *administration publiques* contenant le terme *impôts* situés dans la ville
      de *Lyon*. Vous pouvez également filtrer par ville en utilisant au choix
      les champs `code_postal` ou `code_insee`.

    retrieve:
    Ce point d'accès permet de récupérer les données d'un ERP spécifique, identifié
    par son [identifiant d'URL](https://fr.wikipedia.org/wiki/Slug_(journalisme))
    (*slug*).
    """

    queryset = (
        Erp.objects.published()
        .geolocated()
        .select_related("activite", "accessibilite", "commune_ext", "user")
        .order_by("accessibilite")
    )
    serializer_class = ErpSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    lookup_field = "slug"
    pagination_class = ErpPagination
    filter_backends = [ErpFilterBackend]
    schema = ErpSchema()
