from django.contrib.auth.models import User
from rest_framework import serializers


from erp import schema
from erp.models import (
    Activite,
    Erp,
    Accessibilite,
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


class AccessibiliteSerializer(serializers.HyperlinkedModelSerializer):
    """This is neat."""

    class Meta:
        model = Accessibilite
        exclude = ["created_at", "updated_at"]

    erp = serializers.HyperlinkedRelatedField(
        lookup_field="slug", many=False, read_only=True, view_name="erp-detail"
    )

    def to_representation(self, instance):
        request = self.context.get("request")
        clean = request and request.GET.get("clean") == "true"
        readable = request and request.GET.get("readable") == "true"
        # see https://stackoverflow.com/a/56826004/330911
        # TODO: option pour filtrer les valeurs nulles
        source = super().to_representation(instance)
        repr = {"url": source["url"], "erp": source["erp"]}
        if readable:
            repr["readable_fields"] = []
            repr["datas"] = {}
        for section, data in schema.get_api_fieldsets().items():
            repr[section] = {}
            for field in data["fields"]:
                # clean up empty fields
                if clean and (
                    source[field] is None or source[field] == [] or source[field] == ""
                ):
                    continue
                if readable:
                    repr["readable_fields"].append(field)
                    type_field = schema.get_type(field)
                    if type_field == "boolean":
                        if source[field]:
                            repr["datas"][field] = schema.get_help_text_ui(field)
                        else:
                            repr["datas"][field] = schema.get_help_text_ui_neg(field)
                    elif type_field in ("string", "array", "number"):
                        repr["datas"][
                            field
                        ] = f"{schema.get_help_text_ui(field)} : {schema.get_human_readable_value(field, getattr(instance, field))}"

                else:
                    repr[section][field] = source[field]
        # move/un-nest/clean "commentaire" field if it exists
        try:
            repr["commentaire"] = repr["commentaire"]["commentaire"]
        except KeyError:
            del repr["commentaire"]
        # remove section if entirely empty
        if clean:
            return dict(
                (key, section) for (key, section) in repr.items() if section != {}
            )
        else:
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
            "uuid",
            "activite",
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
            "contact_url",
            "user_type",
            "accessibilite",
            "distance",
            "source_id",
        )
        lookup_field = "slug"
        extra_kwargs = {"url": {"lookup_field": "slug"}}

    activite = ActiviteSerializer(many=False, read_only=True)
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
