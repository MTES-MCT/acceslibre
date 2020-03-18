from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from erp.models import (
    Activite,
    Erp,
    Accessibilite,
    Label,
    EquipementMalentendant,
)

# Useful docs:
# - extra fields: https://stackoverflow.com/a/36697562/330911
# - extra property field: https://stackoverflow.com/questions/17066074/modelserializer-using-model-property#comment89003163_17066237
# - relation serialization: https://www.django-rest-framework.org/api-guide/relations/#slugrelatedfield
# - hyperlinked relation: https://www.django-rest-framework.org/api-guide/relations/#hyperlinkedidentityfield


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]


class EquipementMalentendantSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipementMalentendant
        fields = ["nom"]


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ["nom"]


class AccessibiliteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accessibilite
        exclude = ["id", "erp", "created_at", "updated_at"]

    labels = serializers.SlugRelatedField(
        slug_field="nom", many=True, read_only=True
    )
    accueil_equipements_malentendants = serializers.SlugRelatedField(
        slug_field="nom", many=True, read_only=True
    )


class ActiviteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Activite
        fields = ["nom", "slug"]
        lookup_field = "slug"
        extra_kwargs = {"url": {"lookup_field": "slug"}}


class ActiviteWithCountSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Activite
        fields = ["nom", "slug", "count"]
        lookup_field = "slug"
        extra_kwargs = {"url": {"lookup_field": "slug"}}

    count = serializers.IntegerField()


class ErpSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Erp
        fields = (
            "url",
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
            "accessibilite",
        )
        lookup_field = "slug"
        extra_kwargs = {"url": {"lookup_field": "slug"}}

    activite = ActiviteSerializer(many=False, read_only=True)
    user = serializers.SlugRelatedField(
        slug_field="username", many=False, read_only=True
    )
    adresse = serializers.ReadOnlyField()
    has_accessibilite = serializers.ReadOnlyField()
    accessibilite = AccessibiliteSerializer(many=False, read_only=True)
