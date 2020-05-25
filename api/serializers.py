from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from erp import schema
from erp.models import (
    Activite,
    Erp,
    Accessibilite,
    Label,
)

# Useful docs:
# - extra fields: https://stackoverflow.com/a/36697562/330911
# - extra property field: https://stackoverflow.com/questions/17066074/modelserializer-using-model-property#comment89003163_17066237
# - relation serialization: https://www.django-rest-framework.org/api-guide/relations/#slugrelatedfield
# - hyperlinked relation: https://www.django-rest-framework.org/api-guide/relations/#hyperlinkedidentityfield
# - custom JSON object representation (Solution 2): https://stackoverflow.com/a/56826004/330911
# - distance field serialization: https://stackoverflow.com/a/53307290/330911


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ["nom"]


class AccessibiliteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Accessibilite
        exclude = ["created_at", "updated_at"]

    erp = serializers.HyperlinkedRelatedField(
        lookup_field="slug", many=False, read_only=True, view_name="erp-detail"
    )
    labels = serializers.SlugRelatedField(slug_field="nom", many=True, read_only=True)

    def to_representation(self, instance):
        # see https://stackoverflow.com/a/56826004/330911
        source = super().to_representation(instance)
        repr = {"url": source["url"], "erp": source["erp"]}
        for section, data in schema.get_api_fieldsets().items():
            repr[section] = {}
            for field in data["fields"]:
                if source[field] is not None and source[field] != []:
                    repr[section][field] = source[field]
        # move/un-nest commentaire field
        repr["commentaire"] = repr["commentaire"]["commentaire"]
        return repr


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
            "web_url",
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
            "contact_email",
            "accessibilite",
            "distance",
        )
        lookup_field = "slug"
        extra_kwargs = {"url": {"lookup_field": "slug"}}

    activite = ActiviteSerializer(many=False, read_only=True)
    user = serializers.SlugRelatedField(
        slug_field="username", many=False, read_only=True
    )
    adresse = serializers.ReadOnlyField()
    distance = serializers.SerializerMethodField()
    commune = serializers.SerializerMethodField()
    code_insee = serializers.SerializerMethodField()
    web_url = serializers.SerializerMethodField()

    def get_distance(self, obj):
        if hasattr(obj, "distance"):
            return obj.distance.m

    def get_commune(self, obj):
        if obj.commune_ext:
            return obj.commune_ext.nom
        else:
            return obj.commune

    def get_code_insee(self, obj):
        if obj.commune_ext:
            return obj.commune_ext.code_insee
        else:
            return obj.code_insee

    def get_web_url(self, obj):
        return self.context["request"].build_absolute_uri(obj.get_absolute_url())
