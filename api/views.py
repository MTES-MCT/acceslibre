from rest_framework import viewsets
from rest_framework import permissions

from erp.models import Activite, Erp
from .serializers import ActiviteSerializer, ErpSerializer


class ActiviteViewSet(viewsets.ModelViewSet):
    queryset = Activite.objects.all().order_by("nom")
    serializer_class = ActiviteSerializer
    # https://www.django-rest-framework.org/api-guide/permissions/#api-reference
    permission_classes = [permissions.AllowAny]


class ErpViewSet(viewsets.ModelViewSet):
    queryset = Erp.objects.all().order_by("nom")
    serializer_class = ErpSerializer
    # https://www.django-rest-framework.org/api-guide/permissions/#api-reference
    permission_classes = [permissions.AllowAny]
