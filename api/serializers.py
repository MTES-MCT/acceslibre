from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import gettext as translate
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from erp import schema
from erp.models import Accessibilite, Activite, Erp
from erp.widget_utils import (
    get_audiodescription_label,
    get_deaf_equipment_label,
    get_entrance_label,
    get_outside_path_label,
    get_parking_label,
    get_room_accessible_label,
    get_sound_beacon_label,
    get_staff_label,
    get_wc_label,
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
        fields = ("username",)


class AccessibiliteSerializer(serializers.HyperlinkedModelSerializer):
    """This is neat."""

    class Meta:
        model = Accessibilite
        exclude = ("created_at", "updated_at", "completion_rate")

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
        fields = ("nom", "slug")
        lookup_field = "slug"
        extra_kwargs = {"url": {"lookup_field": "slug"}}


class ActiviteGeoSerializer(ActiviteSerializer):
    class Meta:
        model = Activite
        fields = ("nom", "vector_icon")


class ActiviteWithCountSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Activite
        fields = ["nom", "slug", "count"]
        lookup_field = "slug"
        extra_kwargs = {"url": {"lookup_field": "slug"}}

    count = serializers.IntegerField()


class ErpSerializer(serializers.HyperlinkedModelSerializer):
    activite = ActiviteSerializer(many=False, read_only=True)
    adresse = serializers.ReadOnlyField()
    distance = serializers.SerializerMethodField()
    web_url = serializers.SerializerMethodField()
    accessibilite = AccessibiliteSerializer(many=False, read_only=True)

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
            "ban_id",
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
            "updated_at",
            "created_at",
        )
        lookup_field = "slug"
        extra_kwargs = {"url": {"lookup_field": "slug"}}

    def get_distance(self, obj):
        if hasattr(obj, "distance"):
            return obj.distance.m

    def get_web_url(self, obj):
        return self.context["request"].build_absolute_uri(obj.get_absolute_url())


class ErpGeoSerializer(GeoFeatureModelSerializer):
    activite = ActiviteGeoSerializer(many=False, read_only=True)
    web_url = serializers.SerializerMethodField()

    class Meta:
        model = Erp
        geo_field = "geom"

        fields = ("uuid", "nom", "adresse", "geom", "activite", "web_url")

    def get_web_url(self, obj):
        return obj.get_absolute_uri()


class WidgetSerializer(serializers.Serializer):
    slug = serializers.CharField()
    sections = serializers.SerializerMethodField()

    def get_sections(self, instance):
        access = instance.accessibilite
        sections = [
            {
                "title": translate("stationnement"),
                "labels": [get_parking_label(access)],
                "icon": f"{settings.SITE_ROOT_URL}/static/img/car.png",
            },
            {
                "title": translate("accès"),
                "labels": [label for label in [get_outside_path_label(access), get_entrance_label(access)] if label],
                "icon": f"{settings.SITE_ROOT_URL}/static/img/path.png",
            },
            {
                "title": translate("personnel"),
                "labels": [get_staff_label(access)],
                "icon": f"{settings.SITE_ROOT_URL}/static/img/people.png",
            },
            {
                "title": translate("balise sonore"),
                "labels": [get_sound_beacon_label(access)],
                "icon": f"{settings.SITE_ROOT_URL}/static/img/people.png",
            },
            {
                "title": translate("audiodescription"),
                "labels": [get_audiodescription_label(access)],
                "icon": f"{settings.SITE_ROOT_URL}/static/img/audiodescription.png",
            },
            {
                "title": translate("équipements sourd et malentendant"),
                "labels": [get_deaf_equipment_label(access)],
                "icon": f"{settings.SITE_ROOT_URL}/static/img/assistive-listening-systems.png",
            },
            {
                "title": translate("sanitaire"),
                "labels": [get_wc_label(access)],
                "icon": f"{settings.SITE_ROOT_URL}/static/img/wc.png",
            },
            {
                "title": translate("chambres accessibles"),
                "labels": [get_room_accessible_label(access)],
                "icon": f"{settings.SITE_ROOT_URL}/static/img/chambre_accessible.png",
            },
        ]

        for entry in sections:
            entry["labels"] = [label for label in entry["labels"] if label]

        return [entry for entry in sections if entry["labels"]]
