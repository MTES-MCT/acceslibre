from rest_framework import serializers

from erp.models import Activite, Erp


class ErpSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Erp
        fields = ["nom", "slug", "mots_cles"]


class ActiviteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Activite
        fields = ["nom", "slug"]
