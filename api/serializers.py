from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from erp.models import Activite, Erp

# Useful docs:
# - extra fields: https://stackoverflow.com/a/36697562/330911
# - extra property field: https://stackoverflow.com/questions/17066074/modelserializer-using-model-property#comment89003163_17066237


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]


class ActiviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activite
        fields = ["nom", "slug"]
        lookup_field = "slug"
        extra_kwargs = {"url": {"lookup_field": "slug"}}


class ActiviteWithCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activite
        fields = ["nom", "slug", "count"]
        lookup_field = "slug"
        extra_kwargs = {"url": {"lookup_field": "slug"}}

    count = serializers.IntegerField()


class ErpSerializer(serializers.ModelSerializer):
    class Meta:
        model = Erp
        fields = (
            "activite",
            "user",
            "nom",
            "slug",
            "adresse",
            "commune",
            "code_insee",
            "geom",
            "siret",
            "telephone",
            "site_internet",
            "has_accessibilite",
        )
        lookup_field = "slug"
        extra_kwargs = {"url": {"lookup_field": "slug"}}

    activite = ActiviteSerializer(many=False, read_only=True)
    user = UserSerializer(many=False, read_only=True)
    adresse = serializers.ReadOnlyField()
    has_accessibilite = serializers.ReadOnlyField()
