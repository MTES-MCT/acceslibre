import re

from django.contrib.gis.geos import Point
from django.forms.models import model_to_dict
from rest_framework import serializers

from erp.imports.utils import get_address_query_to_geocode
from erp.models import Accessibilite, Activite, Commune, Erp
from erp.provider import geocoder, sirene

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, code="duplicate")


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
            "source",
            "geoloc_provider",
            "source",
            "source_id",
        )

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
        obj = obj.replace(" ", "")
        obj = obj.replace(" ", "")
        return obj

    def validate_accessibilite(self, obj):
        if not obj:
            raise serializers.ValidationError("Au moins un champ d'accessibilité requis.")

        return obj

    def validate(self, obj):
        if "accessibilite" not in obj:
            raise serializers.ValidationError("Veuillez fournir les données d'accessibilité.")

        if self.instance:
            # if we are updating an ERP, only accessibility and import_email are editable
            self.instance.import_email = obj.get("import_email")
            accessibilite = Accessibilite(**obj["accessibilite"])
            accessibilite.full_clean()
            return model_to_dict(self.instance) | {"accessibilite": model_to_dict(accessibilite)}

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
                obj.pop("latitude", None)
                obj.pop("longitude", None)
                break
            except (RuntimeError, KeyError):
                if i < 2:
                    continue

                if obj.get("latitude") is not None and obj.get("longitude") is not None:
                    self._geom = Point((obj["latitude"], obj["longitude"]))
                    obj.pop("latitude")
                    obj.pop("longitude")
                    break

                raise serializers.ValidationError(f"Adresse non localisable: {address}")

        obj["commune_ext"] = Commune.objects.filter(
            nom__iexact=obj["commune"], code_postaux__contains=[obj["code_postal"]]
        ).first()

        existing = Erp.objects.find_duplicate(
            numero=obj.get("numero"),
            voie=obj.get("voie"),
            lieu_dit=obj.get("lieu_dit"),
            commune=obj["commune"],
            activite=obj["activite"],
        ).first()

        if existing:
            raise DuplicatedExceptionErp([f"Potentiel doublon avec l'ERP : {existing}", existing.pk])

        erp_data = obj.copy()
        erp_data.pop("accessibilite")
        Erp(**erp_data).full_clean(exclude=("source_id", "asp_id", "user", "metadata", "search_vector"))
        Accessibilite(**obj["accessibilite"]).full_clean()
        return obj

    def update(self, instance, validated_data, partial=True):
        # if we are updating an ERP, only accessibility and import_email are editable
        if validated_data.get("import_email"):
            instance.import_email = validated_data["import_email"]
            instance.save(update_fields=["import_email"])

        accessibilite = instance.accessibilite
        for attr in ("id", "erp"):
            validated_data["accessibilite"].pop(attr, False)

        for attr in validated_data["accessibilite"]:
            if validated_data["accessibilite"][attr] is not None:
                setattr(accessibilite, attr, validated_data["accessibilite"][attr])

        accessibilite.save()
        return instance

    def create(self, validated_data):
        accessibilite_data = validated_data.pop("accessibilite")
        erp = Erp.objects.create(**validated_data, geom=self._geom)
        Accessibilite.objects.create(erp=erp, **accessibilite_data)

        return erp
