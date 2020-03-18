from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.pagination import PageNumberPagination

from erp.models import Activite, Erp
from .serializers import (
    ActiviteSerializer,
    ActiviteWithCountSerializer,
    ErpSerializer,
)

# Useful docs
# - permissions: https://www.django-rest-framework.org/api-guide/permissions/#api-reference
# - queryable slugs: https://stackoverflow.com/a/32209005/330911
# - pagination style: https://www.django-rest-framework.org/api-guide/pagination/#modifying-the-pagination-style


class ActivitePagination(PageNumberPagination):
    page_size = 300


class ActiviteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Activite.objects.order_by("nom")
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = ActiviteWithCountSerializer
    lookup_field = "slug"
    pagination_class = ActivitePagination

    def get_queryset(self):
        queryset = self.queryset
        commune = self.request.query_params.get(
            "commune", None  # FIXME/ should use slug
        )
        if commune is not None:
            queryset = queryset.in_commune(commune)
        return queryset.with_erp_counts()


class ErpPagination(PageNumberPagination):
    page_size = 20


class ErpViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Erp.objects.published()
        .geolocated()
        .select_related("activite")
        .select_related("accessibilite")
        .order_by("accessibilite")
    )
    serializer_class = ErpSerializer
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    lookup_field = "slug"
    pagination_class = ErpPagination

    def get_queryset(self):
        queryset = self.queryset
        # Commune
        commune = self.request.query_params.get(
            "commune", None  # FIXME/ should use slug
        )
        if commune is not None:
            queryset = queryset.in_commune(commune)
        # Activité
        activite = self.request.query_params.get("activite", None)
        if activite is not None:
            queryset = queryset.having_activite(activite)
        # Search
        search_terms = self.request.query_params.get("q", None)
        if search_terms is not None:
            queryset = queryset.search(search_terms)
        return queryset
