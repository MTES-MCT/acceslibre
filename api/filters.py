from datetime import datetime, timedelta

from django.contrib.gis.geos import Point
from django.db.models import Q
from rest_framework.filters import BaseFilterBackend, OrderingFilter
from rest_framework_gis.filters import InBBoxFilter

from erp.provider import geocoder
from erp.provider.search import filter_erps_by_equipments


class ZoneFilter(InBBoxFilter):
    bbox_param = "zone"

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": self.bbox_param,
                "required": False,
                "in": "query",
                "description": "Bounding box to search on, following format `min_longitude,min_latitude,max_longitude,max_latitude` (for ex. ?zone=4.849022,44.885530,4.982661,44.963994)",
                "schema": {
                    "type": "array",
                    "items": {"type": "float"},
                    "minItems": 4,
                    "maxItems": 4,
                    "example": [-180, -90, 180, 90],
                },
                "style": "form",
                "explode": False,
            },
        ]


class ErpFilter(OrderingFilter, BaseFilterBackend):
    # Work around DRF issue #6886 by always adding the primary key as last order field.
    # See https://github.com/encode/django-rest-framework/issues/6886
    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        pk = queryset.model._meta.pk.name

        if ordering is None:
            return (f"-{pk}",)
        return list(ordering) + [f"-{pk}"]

    # FIXME: do NOT apply filters on details view
    def filter_queryset(self, request, queryset, view):
        ordered = False
        use_distinct = False

        with_drafts = request.query_params.get("with_drafts", False)
        if not with_drafts:
            queryset = queryset.published()

        commune = request.query_params.get("commune", None)
        if commune is not None:
            queryset = queryset.filter(commune__unaccent__icontains=commune)

        code_postal = request.query_params.get("code_postal", None)
        if code_postal is not None:
            queryset = queryset.filter(code_postal=code_postal)

        code_insee = request.query_params.get("code_insee", None)
        if code_insee is not None:
            queryset = queryset.filter(commune_ext__code_insee=code_insee)

        ban_id = request.query_params.get("ban_id", None)
        if ban_id is not None:
            queryset = queryset.filter(ban_id=ban_id)

        activite = request.query_params.get("activite", None)
        if activite is not None:
            queryset = queryset.having_activite(activite)

        siret = request.query_params.get("siret", None)
        if siret is not None:
            queryset = queryset.filter(siret=siret)

        search_terms = request.query_params.get("q", None)
        if search_terms is not None:
            use_distinct = False
            ordered = True
            queryset = queryset.search_what(search_terms)

        source = request.query_params.get("source", None)
        if source is not None:
            queryset = queryset.filter(source__iexact=source)

        source_id = request.query_params.get("source_id", None)
        if source_id is not None:
            queryset = queryset.filter(source_id__iexact=source_id)

        asp_id = request.query_params.get("asp_id", None)
        if asp_id is not None:
            queryset = queryset.filter(asp_id__iexact=asp_id)

        asp_id_not_null = request.query_params.get("asp_id_not_null", None)
        if asp_id_not_null is not None:
            if asp_id_not_null == "true":
                queryset = queryset.exclude(asp_id__isnull=True).exclude(asp_id="")
            else:
                queryset = queryset.filter(asp_id__isnull=True)

        uuid = request.query_params.get("uuid", None)
        if uuid is not None:
            queryset = queryset.filter(uuid=uuid)

        around = geocoder.parse_coords(request.query_params.get("around"))
        if around is not None:
            lat, lon = around
            queryset = queryset.nearest(Point(lon, lat, srid=4326))
            use_distinct = False
            ordered = True

        number_of_days = request.query_params.get("created_or_updated_in_last_days", None)
        if number_of_days is not None:
            days_ago = datetime.now() - timedelta(days=int(number_of_days))
            queryset = queryset.filter(
                Q(created_at__gt=days_ago)
                | Q(updated_at__gt=days_ago)
                | Q(accessibilite__created_at__gt=days_ago)
                | Q(accessibilite__updated_at__gt=days_ago)
            )
            use_distinct = True

        if use_distinct:
            queryset = queryset.distinct("id", "nom")

        if not ordered:
            ordering = self.get_ordering(request, queryset, view)
            queryset = queryset.order_by(*ordering)

        return queryset


class EquipmentFilter(BaseFilterBackend):
    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "equipments",
                "in": "query",
                "required": False,
                "description": "List of equipments to filter on (for ex. `?equipments=having_public_transportation&equipments=having_adapted_parking`)",
                "schema": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "example": ["having_public_transportation", "having_adapted_parking"],
                },
            },
        ]

    def filter_queryset(self, request, queryset, *args, **kwargs):
        equipments = request.query_params.getlist("equipments")
        return filter_erps_by_equipments(queryset, equipments)
