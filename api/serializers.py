from django.contrib.auth.models import User
from rest_framework import serializers

from erp import schema
from erp.models import Accessibilite, Activite, Erp

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

    erp = serializers.HyperlinkedRelatedField(lookup_field="slug", many=False, read_only=True, view_name="erp-detail")

    def _readable_value(self, source, instance, repr, field, section):
        repr["readable_fields"].append(field)
        if schema.get_type(field) == "boolean":
            if source[field] is True:
                repr["datas"][section][field] = schema.get_help_text_ui(field)
            elif source[field] is False:
                repr["datas"][section][field] = schema.get_help_text_ui_neg(field)
            else:
                repr["datas"][section][field] = None
        else:
            repr["datas"][section][field] = "{} : {}".format(
                schema.get_help_text_ui(field),
                schema.get_human_readable_value(field, getattr(instance, field)),
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
            if readable:
                repr["datas"][section] = {}
            else:
                repr[section] = {}
            for field in data["fields"]:
                # clean up empty fields
                if clean and source[field] in (None, [], ""):
                    continue
                if readable:
                    self._readable_value(source, instance, repr, field, section)
                else:
                    repr[section][field] = source[field]

        if "commentaire" in repr:
            comm_field = repr["commentaire"]
        else:
            comm_field = repr["datas"]["commentaire"]
        try:
            comm_field = comm_field["commentaire"]
        except KeyError:
            del comm_field
        # remove section if entirely empty
        if readable and clean:
            repr["datas"] = dict((key, section) for key, section in repr["datas"].items() if section != {})
        if clean:
            return dict((key, section) for key, section in repr.items() if section != {})
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
            "code_postal",
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
            "asp_id",
        )
        lookup_field = "slug"
        extra_kwargs = {"url": {"lookup_field": "slug"}}

    activite = ActiviteSerializer(many=False, read_only=True)
    adresse = serializers.ReadOnlyField()
    distance = serializers.SerializerMethodField()
    commune = serializers.SerializerMethodField()
    code_insee = serializers.SerializerMethodField()
    web_url = serializers.SerializerMethodField()
    accessibilite = AccessibiliteSerializer(many=False, read_only=True)

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
