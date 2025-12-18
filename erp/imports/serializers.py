import re

from django.contrib.gis.geos import Point
from django.forms.models import model_to_dict
from rest_framework import serializers

from api.serializers import ExternalSourceSerializer
from erp.imports.utils import get_address_query_to_geocode
from erp.models import Accessibilite, Activite, Commune, Erp, ExternalSource
from erp.provider import geocoder, sirene
from erp.schema import FIELDS

TRUE_VALUES = ["true", "True", "TRUE", "1", "vrai", "Vrai", "VRAI", "oui", "Oui", "OUI", True]
FALSE_VALUES = ["false", "False", "FALSE", "0", "faux", "Faux", "FAUX", "non", "Non", "NON", False]


class NullBooleanField(serializers.Field):
    def to_internal_value(self, data):
        if data in TRUE_VALUES:
            return True
        if data in FALSE_VALUES:
            return False
        return None

    def to_representation(self, value):
        if value in TRUE_VALUES:
            return True
        if value in FALSE_VALUES:
            return False
        return None


class DuplicatedExceptionErp(serializers.ValidationError):
    default_detail = "Doublon avec un ERP en base"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, code="duplicate")


class PermanentlyClosedExceptionErp(serializers.ValidationError):
    default_detail = "Doublon avec un ERP définitivement clôs"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, code="permanently_closed")


class AccessibilityImportSerializer(serializers.ModelSerializer):
    # NOTE: all fields which have choices in BOOLEAN_CHOICES, NULLABLE_BOOLEAN_CHOICES, NULLABLE_OR_NA_BOOLEAN_CHOICES
    #       maybe dynamiccally declarable.
    transport_station_presence = NullBooleanField(required=False, allow_null=True)
    stationnement_presence = NullBooleanField(required=False, allow_null=True)
    stationnement_pmr = NullBooleanField(required=False, allow_null=True)
    stationnement_ext_presence = NullBooleanField(required=False, allow_null=True)
    stationnement_ext_pmr = NullBooleanField(required=False, allow_null=True)
    cheminement_ext_presence = NullBooleanField(required=False, allow_null=True)
    cheminement_ext_terrain_stable = NullBooleanField(required=False, allow_null=True)
    cheminement_ext_plain_pied = NullBooleanField(required=False, allow_null=True)
    cheminement_ext_ascenseur = NullBooleanField(required=False, allow_null=True)
    cheminement_ext_reperage_marches = NullBooleanField(required=False, allow_null=True)
    cheminement_ext_main_courante = NullBooleanField(required=False, allow_null=True)
    cheminement_ext_pente_presence = NullBooleanField(required=False, allow_null=True)
    cheminement_ext_bande_guidage = NullBooleanField(required=False, allow_null=True)
    cheminement_ext_retrecissement = NullBooleanField(required=False, allow_null=True)
    entree_reperage = NullBooleanField(required=False, allow_null=True)
    entree_porte_presence = NullBooleanField(required=False, allow_null=True)
    entree_vitree = NullBooleanField(required=False, allow_null=True)
    entree_vitree_vitrophanie = NullBooleanField(required=False, allow_null=True)
    entree_plain_pied = NullBooleanField(required=False, allow_null=True)
    entree_ascenseur = NullBooleanField(required=False, allow_null=True)
    entree_marches_reperage = NullBooleanField(required=False, allow_null=True)
    entree_marches_main_courante = NullBooleanField(required=False, allow_null=True)
    entree_dispositif_appel = NullBooleanField(required=False, allow_null=True)
    entree_balise_sonore = NullBooleanField(required=False, allow_null=True)
    entree_aide_humaine = NullBooleanField(required=False, allow_null=True)
    entree_pmr = NullBooleanField(required=False, allow_null=True)
    accueil_visibilite = NullBooleanField(required=False, allow_null=True)
    accueil_cheminement_plain_pied = NullBooleanField(required=False, allow_null=True)
    accueil_cheminement_ascenseur = NullBooleanField(required=False, allow_null=True)
    accueil_cheminement_reperage_marches = NullBooleanField(required=False, allow_null=True)
    accueil_cheminement_main_courante = NullBooleanField(required=False, allow_null=True)
    accueil_retrecissement = NullBooleanField(required=False, allow_null=True)
    accueil_chambre_douche_plain_pied = NullBooleanField(required=False, allow_null=True)
    accueil_chambre_douche_siege = NullBooleanField(required=False, allow_null=True)
    accueil_chambre_douche_barre_appui = NullBooleanField(required=False, allow_null=True)
    accueil_chambre_sanitaires_barre_appui = NullBooleanField(required=False, allow_null=True)
    accueil_chambre_sanitaires_espace_usage = NullBooleanField(required=False, allow_null=True)
    accueil_chambre_numero_visible = NullBooleanField(required=False, allow_null=True)
    accueil_chambre_equipement_alerte = NullBooleanField(required=False, allow_null=True)
    accueil_chambre_accompagnement = NullBooleanField(required=False, allow_null=True)
    accueil_audiodescription_presence = NullBooleanField(required=False, allow_null=True)
    accueil_equipements_malentendants_presence = NullBooleanField(required=False, allow_null=True)
    sanitaires_presence = NullBooleanField(required=False, allow_null=True)
    sanitaires_adaptes = NullBooleanField(required=False, allow_null=True)
    conformite = NullBooleanField(required=False, allow_null=True)

    class Meta:
        model = Accessibilite
        fields = "__all__"


class ErpImportSerializer(serializers.ModelSerializer):
    activite = serializers.SlugRelatedField(queryset=Activite.objects.all(), slug_field="nom")
    commune = serializers.CharField(required=True)
    accessibilite = AccessibilityImportSerializer(many=False, required=True)
    latitude = serializers.FloatField(min_value=-90, max_value=90, required=False, allow_null=True, default=None)
    longitude = serializers.FloatField(min_value=-180, max_value=180, required=False, allow_null=True, default=None)
    sources = ExternalSourceSerializer(many=True, required=False, default=[])

    _geom: Point = None

    class Meta:
        model = Erp
        fields = (
            "nom",
            "code_postal",
            "commune",
            "numero",
            "slug",
            "voie",
            "lieu_dit",
            "code_insee",
            "siret",
            "contact_url",
            "activite",
            "import_email",
            "site_internet",
            "telephone",
            "accessibilite",
            "latitude",
            "longitude",
            "geoloc_provider",
            "source",
            "source_id",
            "ban_id",
            "asp_id",
            "sources",
        )

    def _ensure_no_duplicate(self, obj):
        existing = None

        if "source" in obj and "source_id" in obj:
            existing = Erp.objects.filter(sources__source=obj["source"], sources__source_id=obj["source_id"])

        if "sources" in obj:
            for source in obj["sources"]:
                if "source" in source and "source_id" in source:
                    existing = Erp.objects.filter(
                        sources__source=source["source"], sources__source_id=source["source_id"]
                    )
                    if existing:
                        break

        if not existing:
            existing = Erp.objects.find_duplicate(
                numero=obj.get("numero"),
                commune=obj["commune"],
                activite=obj["activite"],
                voie=obj.get("voie"),
                lieu_dit=obj.get("lieu_dit"),
            )

        if any([erp.permanently_closed for erp in existing]):
            raise PermanentlyClosedExceptionErp()

        if erp := existing.published().first():
            raise DuplicatedExceptionErp([f"Potentiel doublon par activité/adresse postale avec l'ERP : {erp}", erp.pk])

        existing = Erp.objects.nearest(point=self._geom, max_radius_km=0.075).filter(
            nom__lower__in=(obj["nom"].lower(), obj["nom"].lower().replace("-", " "))
        )

        if any([erp.permanently_closed for erp in existing]):
            raise PermanentlyClosedExceptionErp()

        if erp := existing.published().first():
            raise DuplicatedExceptionErp([f"Potentiel doublon par nom/75m alentours avec l'ERP : {erp}", erp.pk])

    def validate_nom(self, value):
        cleaned = (
            str(value).replace("\n", " ").replace("«", "").replace("»", "").replace("’", "'").replace('"', "").strip()
        )
        # replace multiple spaces with one
        return " ".join(cleaned.split())

    def validate_siret(self, obj):
        if not obj:
            return

        cleaned = sirene.validate_siret(obj)
        if not cleaned:
            raise serializers.ValidationError("Le siret doit être valide.")

        return cleaned

    def validate_code_postal(self, obj):
        # source: https://rgxdb.com/
        if not re.match(r"^(?:0[1-9]|[1-8]\d|9[0-8])\d{3}$", obj):
            raise serializers.ValidationError("Le code postal n'est pas valide.")

        return obj

    def validate_telephone(self, obj):
        # weird invisible char
        if not obj:
            return obj

        obj = obj.replace(" ", "")
        obj = obj.replace(" ", "")
        return obj

    def validate_accessibilite(self, obj):
        if not obj:
            raise serializers.ValidationError("Au moins un champ d'accessibilité requis.")

        return obj

    def _handle_children_reinit(self, accessibilite_instance, field_name):
        field_config = FIELDS.get(field_name)
        if not field_config or not field_config.get("children"):
            return

        current_value = getattr(accessibilite_instance, field_name)
        trigger_values = field_config.get("value_to_display_children", [])

        if str(current_value) not in trigger_values:
            for child_name in field_config.get("children"):
                field_obj = accessibilite_instance._meta.get_field(child_name)
                default_value = field_obj.get_default()
                if callable(default_value):
                    default_value = default_value()

                setattr(accessibilite_instance, child_name, default_value)

                self._handle_children_reinit(accessibilite_instance, child_name)

    def validate(self, obj):
        if "accessibilite" not in obj:
            raise serializers.ValidationError("Veuillez fournir les données d'accessibilité.")

        if not self.partial:
            if self.instance:
                # if we are updating an ERP, only accessibility, asp_id and import_email are editable
                self.instance.import_email = obj.get("import_email")
                self.instance.asp_id = obj.get("asp_id")
                accessibilite = Accessibilite(**obj["accessibilite"])
                accessibilite.full_clean()

                sources_data_list = []
                sources_data = obj.get("sources") or []
                for source_data in sources_data:
                    external_source = ExternalSource(**source_data)
                    external_source.full_clean(exclude=("erp",))
                    sources_data_list.append(model_to_dict(external_source))

                return (
                    model_to_dict(self.instance)
                    | {"accessibilite": model_to_dict(accessibilite)}
                    | {"sources": sources_data_list}
                )

            if not obj.get("voie") and not obj.get("lieu_dit"):
                raise serializers.ValidationError("Veuillez entrer une voie OU un lieu-dit")

            for i in range(3):
                try:
                    address = get_address_query_to_geocode(obj)
                    locdata = geocoder.geocode(address, postcode=obj["code_postal"])
                    if not locdata:
                        raise RuntimeError
                    self._geom = locdata["geom"]
                    obj["voie"] = locdata["voie"]
                    obj["lieu_dit"] = locdata["lieu_dit"]
                    obj["code_postal"] = locdata["code_postal"]
                    obj["commune"] = locdata["commune"]
                    obj["code_insee"] = locdata["code_insee"]
                    obj["geoloc_provider"] = locdata["provider"]
                    obj["numero"] = locdata["numero"]
                    obj["ban_id"] = locdata.get("ban_id")
                    obj.pop("latitude", None)
                    obj.pop("longitude", None)
                    break
                except (RuntimeError, KeyError):
                    if i < 2:
                        continue

                    if obj.get("latitude") is not None and obj.get("longitude") is not None:
                        self._geom = Point((obj["longitude"], obj["latitude"]), srid=4326)
                        obj.pop("latitude")
                        obj.pop("longitude")
                        break

                    raise serializers.ValidationError(f"Adresse non localisable: {address}")

            obj["commune_ext"] = Commune.objects.filter(
                nom__iexact=obj["commune"], code_postaux__contains=[obj["code_postal"]]
            ).first()

            self._ensure_no_duplicate(obj)

            erp_data = obj.copy()
            erp_data.pop("accessibilite")
            erp_data.pop("sources")

            Erp(**erp_data).full_clean(exclude=("source_id", "asp_id", "user", "metadata", "search_vector"))

        if "accessibilite" in obj:
            Accessibilite(**obj["accessibilite"]).full_clean()

        sources_data = obj.get("sources") or []
        for source_data in sources_data:
            ExternalSource(**source_data).full_clean(exclude=("erp",))

        return obj

    def update(self, instance, validated_data):
        enrich_only = self.context.get("enrich_only") or False
        raw_data = self.initial_data

        # if we are updating an ERP, only accessibility, asp_id and import_email are editable
        if validated_data.get("import_email"):
            instance.import_email = validated_data["import_email"]
            instance.save(update_fields=["import_email"])

        if validated_data.get("asp_id"):
            instance.asp_id = validated_data["asp_id"]
            instance.save(update_fields=["asp_id"])

        accessibilite = instance.accessibilite
        acc_data = validated_data.get("accessibilite", {})
        raw_acc_data = raw_data.get("accessibilite", {})

        for attr, new_value in acc_data.items():
            if attr in ("id", "erp"):
                continue

            if enrich_only and getattr(accessibilite, attr, None) is not None:
                continue

            if self.partial and attr in raw_acc_data and raw_acc_data[attr] in (None, "", [], ()):
                continue

            if not enrich_only or new_value not in (None, [], ()):
                setattr(accessibilite, attr, new_value)
                self._handle_children_reinit(accessibilite, attr)

        accessibilite.save()

        sources_data = validated_data.pop("sources", [])
        self._create_or_update_sources(instance, sources_data)
        return instance

    def create(self, validated_data):
        accessibilite_data = validated_data.pop("accessibilite")
        sources_data = validated_data.pop("sources", [])

        erp = Erp.objects.create(**validated_data, geom=self._geom)
        Accessibilite.objects.create(erp=erp, **accessibilite_data)
        self._create_or_update_sources(erp, sources_data)

        return erp

    def _create_or_update_sources(self, erp, sources_data):
        for source_data in sources_data:
            ExternalSource.objects.filter(erp=erp, source=source_data["source"]).delete()
            ExternalSource.objects.create(erp_id=erp.pk, **source_data)
