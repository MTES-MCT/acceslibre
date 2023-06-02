from functools import reduce

from better_profanity import profanity
from django import forms
from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError
from django.db.models import F
from django.forms import widgets
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as translate
from django.utils.translation import gettext_lazy as translate_lazy

from compte.models import UserStats
from erp import schema
from erp.imports.utils import get_address_query_to_geocode
from erp.models import Accessibilite, Activite, Commune, Erp
from erp.provider import departements, geocoder


def bool_radios():
    return forms.RadioSelect(attrs={"class": "inline"})


def get_widgets_for_accessibilite():
    field_names = schema.get_nullable_bool_fields()
    return dict([(f, bool_radios()) for f in field_names])


class ContribAccessibiliteForm(forms.ModelForm):
    # Note: defining `labels` and `help_texts` in `Meta` doesn't work with custom
    # fields, hence why we set them up manually for each fields.

    accueil_audiodescription = forms.MultipleChoiceField(
        required=False,
        choices=schema.AUDIODESCRIPTION_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label=schema.get_label("accueil_audiodescription"),
        help_text=schema.get_help_text("accueil_audiodescription"),
    )
    accueil_equipements_malentendants = forms.MultipleChoiceField(
        required=False,
        choices=schema.EQUIPEMENT_MALENTENDANT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label=schema.get_label("accueil_equipements_malentendants"),
        help_text=schema.get_help_text("accueil_equipements_malentendants"),
    )
    entree_porte_presence = forms.ChoiceField(
        required=False,
        initial=True,
        label=schema.get_label("entree_porte_presence"),
        help_text=schema.get_help_text("entree_porte_presence"),
        choices=[(True, "Oui"), (False, "Non")],
        widget=forms.RadioSelect(attrs={"class": "inline"}),
    )
    entree_dispositif_appel_type = forms.MultipleChoiceField(
        required=False,
        choices=schema.DISPOSITIFS_APPEL_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label=schema.get_label("entree_dispositif_appel_type"),
        help_text=schema.get_help_text("entree_dispositif_appel_type"),
    )
    labels_familles_handicap = forms.MultipleChoiceField(
        required=False,
        choices=schema.HANDICAP_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label=schema.get_label("labels_familles_handicap"),
        help_text=schema.get_help_text("labels_familles_handicap"),
    )
    labels = forms.MultipleChoiceField(
        required=False,
        choices=schema.LABEL_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label=schema.get_label("labels"),
        help_text=schema.get_help_text("labels"),
    )
    _user = None

    class Meta:
        model = Accessibilite
        exclude = ["pk"] + schema.get_conditional_fields()
        widgets = get_widgets_for_accessibilite()
        labels = schema.get_labels()
        help_texts = schema.get_help_texts()
        required = schema.get_required_fields()

    def __init__(self, *args, **kwargs):
        self._user = kwargs.pop("user", False)
        super().__init__(*args, **kwargs)

    def clean_accueil_equipements_malentendants(self):
        if (
            "accueil_equipements_malentendants_presence" in self.cleaned_data
            and self.cleaned_data["accueil_equipements_malentendants_presence"] is not True
        ):
            return None
        return self.cleaned_data["accueil_equipements_malentendants"]

    def clean_accueil_audiodescription(self):
        if (
            "accueil_audiodescription_presence" in self.cleaned_data
            and self.cleaned_data["accueil_audiodescription_presence"] is not True
        ):
            return None
        return self.cleaned_data["accueil_audiodescription"]

    def clean(self):
        cleaned_data = super().clean()
        profanity_word_loaded = False
        for free_text in schema.get_free_text_fields():
            if not cleaned_data.get(free_text):
                continue

            if not profanity_word_loaded:
                profanity.load_censor_words_from_file(settings.FRENCH_PROFANITY_WORDLIST)

            if profanity.contains_profanity(cleaned_data[free_text]):
                cleaned_data.pop(free_text)
                if self._user:
                    user_stats, _ = UserStats.objects.get_or_create(user=self._user)
                    user_stats.nb_profanities = F("nb_profanities") + 1
                    user_stats.save(update_fields=("nb_profanities",))
        return cleaned_data


class ContribAccessibiliteHotelsForm(ContribAccessibiliteForm):
    class Meta:
        model = Accessibilite
        exclude = ("pk",)
        widgets = get_widgets_for_accessibilite()
        labels = schema.get_labels(include_conditional=True)
        help_texts = schema.get_help_texts(include_conditional=True)
        required = schema.get_required_fields()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in (
            "accueil_audiodescription_presence",
            "accueil_audiodescription",
            "sanitaires_presence",
            "sanitaires_adaptes",
        ):
            self.fields.pop(field, None)


class AdminAccessibiliteForm(ContribAccessibiliteForm):
    # Note: defining `labels` and `help_texts` in `Meta` doesn't work with custom
    # fields, hence why we set them up manually for each fields.
    class Meta:
        model = Accessibilite
        exclude = ["pk"]
        widgets = get_widgets_for_accessibilite()
        labels = schema.get_labels(include_conditional=True)
        help_texts = schema.get_help_texts(include_conditional=True)
        required = schema.get_required_fields()

    sanitaires_adaptes = forms.ChoiceField(
        required=False,
        label=schema.get_label("sanitaires_adaptes"),
        help_text=schema.get_help_text("sanitaires_adaptes"),
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "inline"}),
    )

    def clean_accueil_equipements_malentendants(self):
        if (
            "accueil_equipements_malentendants_presence" in self.cleaned_data
            and self.cleaned_data["accueil_equipements_malentendants_presence"] is not True
        ):
            return None
        return self.cleaned_data["accueil_equipements_malentendants"]

    def clean_accueil_audiodescription(self):
        if (
            "accueil_audiodescription_presence" in self.cleaned_data
            and self.cleaned_data["accueil_audiodescription_presence"] is not True
        ):
            return None
        return self.cleaned_data["accueil_audiodescription"]

    def clean_sanitaires_adaptes(self):
        value = self.cleaned_data["sanitaires_adaptes"]
        if value == "":
            return None
        return value


class AdminActiviteForm(forms.ModelForm):
    class Meta:
        model = Activite
        exclude = ("pk",)

    mots_cles = SimpleArrayField(
        forms.CharField(),
        widget=widgets.Textarea(),
        delimiter="\n",
        required=False,
        help_text=translate_lazy("Un mot-clé par ligne"),
    )

    def save(self, commit=True):
        m = super(AdminActiviteForm, self).save(commit=False)
        m.nom = m.nom.capitalize()
        m.save()
        Activite.reorder()
        m.refresh_from_db()
        return m


class AdminCommuneForm(forms.ModelForm):
    class Meta:
        model = Commune
        exclude = ("pk",)

    code_postaux = SimpleArrayField(
        forms.CharField(),
        widget=widgets.Textarea(),
        delimiter="\n",
        required=False,
        help_text=translate_lazy("Un code postal par ligne"),
    )


class BaseErpForm(forms.ModelForm):
    def __init__(self, *args, geocode=None, **kwargs):
        self.do_geocode = geocode if geocode else geocoder.geocode
        super().__init__(*args, **kwargs)

    def adresse_changed(self):
        try:
            return (
                self.cleaned_data["numero"] != self.instance.numero
                or self.cleaned_data["voie"] != self.instance.voie
                or self.cleaned_data["lieu_dit"] != self.instance.lieu_dit
                or self.cleaned_data["code_postal"] != self.instance.code_postal
                or self.cleaned_data["commune"] != self.instance.commune
            )
        except KeyError:
            return True

    def format_error(self, message):
        signalement_url = reverse("contact_topic", kwargs={"topic": "bug"})
        return mark_safe(
            translate(
                f'{message}. Veuillez vérifier votre saisie ou <a href="{signalement_url}" '
                'target="_blank">signaler une erreur</a>.'
            )
        )

    def raise_validation_error(self, field, message):
        raise ValidationError({field: self.format_error(message)})

    def geocode(self):
        adresse = get_address_query_to_geocode(self.cleaned_data)
        code_postal = self.cleaned_data.get("code_postal", "").strip() or None
        departement = code_postal[:2] if code_postal and len(code_postal) == 5 else None
        commune_input = self.cleaned_data.get("commune")
        commune = Commune.objects.search_by_nom_code_postal(commune_input, code_postal).first()
        locdata = None
        try:
            locdata = self.do_geocode(adresse, citycode=commune.code_insee if commune else None)
        except RuntimeError as err:
            raise ValidationError(err)

        # Check for geocoded results
        if not locdata or locdata.get("geom") is None:
            self.raise_validation_error("voie", f"Adresse non localisable : {adresse} ({code_postal})")

        # Ensure picking the right postcode
        if code_postal and locdata["code_postal"] and code_postal != locdata["code_postal"]:
            dpt_result = locdata["code_postal"][:2]
            if departement != dpt_result:
                # Different departement, too risky to consider it valid; raise an error
                self.raise_validation_error(
                    "code_postal",
                    mark_safe(
                        translate(
                            f"Cette adresse n'est pas localisable au code postal {code_postal} "
                            f"(mais l'est au code {locdata['code_postal']})"
                        )
                    ),
                )

        # Validate code insee
        if self.cleaned_data.get("code_insee") and self.cleaned_data["code_insee"] != locdata["code_insee"]:
            self.raise_validation_error(
                "code_insee",
                translate("Cette adresse n'est pas localisable au code INSEE {}").format(
                    self.cleaned_data["code_insee"]
                ),
            )

        # Validate house number, if any
        if self.cleaned_data.get("numero"):
            if locdata["numero"]:
                self.cleaned_data["numero"] = locdata["numero"]

        # Apply changes
        self.cleaned_data["geom"] = locdata["geom"]
        self.cleaned_data["voie"] = locdata["voie"]
        self.cleaned_data["lieu_dit"] = locdata["lieu_dit"]
        self.cleaned_data["code_postal"] = locdata["code_postal"]
        self.cleaned_data["commune"] = locdata["commune"]
        self.cleaned_data["code_insee"] = locdata["code_insee"]
        self.cleaned_data["geoloc_provider"] = locdata["provider"]


class AdminErpForm(BaseErpForm):
    class Meta:
        model = Erp
        exclude = (
            "pk",
            "uuid",
            "search_vector",
            "source",
            "source_id",
            "metadata",
        )

    def clean(self):
        if self.cleaned_data["geom"] is None or self.adresse_changed():
            self.geocode()


class ViewAccessibiliteForm(AdminAccessibiliteForm):
    """This form is used to render Accessibilite data in Erp details pages, and is
    probably one of the most hairy piece of code and logic from the whole app. This
    is due to the inherent complexity of the professional accessibility domain
    where words, concepts and their formulation — which HAVE to be cognitively
    accessible themselves — are highly important."""

    class Meta:
        model = Accessibilite
        exclude = (
            "pk",
            "erp",
        )

    fieldsets = schema.get_form_fieldsets()

    def get_accessibilite_data(self, flatten=False):
        data = {}
        for section, section_info in self.fieldsets.items():
            data[section] = {
                "icon": section_info["icon"],
                "tabid": section_info["tabid"],
                "description": section_info["description"],
                "edit_route": section_info["edit_route"],
                "fields": [],
            }
            section_fields = section_info["fields"]
            for field_data in section_fields:
                field = self[field_data["id"]]
                field_value = field.value()
                warning = False
                if "warn_if" in field_data and field_data["warn_if"] is not None:
                    if callable(field_data["warn_if"]):
                        warning = field_data["warn_if"](field_value, self.instance)
                    else:
                        warning = field_value == field_data["warn_if"]
                label, values = self.get_label_and_values(
                    field.name, field_value, field_data["choices"], field_data["unit"]
                )
                data[section]["fields"].append(
                    {
                        "name": field.name,
                        "label": label,
                        "value": field_value,
                        "values": values,
                        "warning": warning,
                        "is_comment": field.field.widget.template_name.endswith("textarea.html"),
                    }
                )
            # Discard empty sections to avoid rendering empty menu items
            empty_section = all(self[f["id"]].value() in [None, "", []] for f in section_fields)
            if empty_section:
                data.pop(section)
        if flatten:
            return reduce(lambda x, y: x + y, (s["fields"] for (_, s) in data.items()), [])
        else:
            return data

    def get_label_and_values(self, name, value, choices, unit=""):
        "Computes rephrased label and optional values to render on the frontend for a given field."
        values = self.get_display_values(name, value, choices, unit)
        if name == "accueil_personnels" and value == schema.PERSONNELS_AUCUN:
            label = schema.get_help_text_ui_neg(name)
            values = []
        elif name == "cheminement_ext_devers" and value == schema.DEVERS_AUCUN:
            label = schema.get_help_text_ui_neg(name)
            values = []
        elif name == "sanitaires_adaptes" and value is False:
            label = schema.get_help_text_ui_neg(name)
            values = []
        elif name == "sanitaires_adaptes" and value is not None and value is True:
            label = schema.get_help_text_ui(name)
            values = []
        elif (
            name
            in [
                "cheminement_ext_rampe",
                "entree_marches_rampe",
                "accueil_cheminement_rampe",
            ]
            and value == schema.RAMPE_AUCUNE
        ):
            label = schema.get_help_text_ui_neg(name)
            values = []
        elif (
            name
            in [
                "cheminement_ext_nombre_marches",
                "entree_marches",
                "accueil_cheminement_nombre_marches",
                "accueil_chambre_nombre_accessibles",
            ]
            and value == 0
        ):
            label = schema.get_help_text_ui_neg(name)
            values = []
        elif value:
            label = schema.get_help_text_ui(name)
        else:
            label = schema.get_help_text_ui_neg(name)
        return label, values

    def get_display_values(self, name, value, choices, unit=""):
        if type(value) == bool:
            return None
        try:
            value = getattr(self.instance, f"get_{name}_display")()
        except AttributeError:
            # for some reason, ArrayField doesn't expose a get_FIELD_display method…
            value = getattr(Accessibilite, name).field.value_from_object(self.instance)
            if choices:
                choices_dict = dict(choices)
                return [choices_dict[v] for v in value] if value else []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [value]
        if isinstance(value, int):
            return [f"{value} {unit}{'s' if value > 1 else ''}"]
        return None


class BasePublicErpInfosForm(BaseErpForm):
    lat = forms.DecimalField(widget=forms.HiddenInput)
    lon = forms.DecimalField(widget=forms.HiddenInput)
    activite = forms.ModelChoiceField(label=translate_lazy("Activité"), queryset=Activite.objects.order_by("position"))
    nouvelle_activite = forms.CharField(widget=forms.TextInput)
    asp_id = forms.CharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Erp
        fields = (
            "source",
            "source_id",
            "asp_id",
            "geom",
            "nom",
            "activite",
            "numero",
            "voie",
            "lieu_dit",
            "code_postal",
            "commune",
            "contact_email",
            "site_internet",
            "telephone",
            "contact_url",
            "geoloc_provider",
            "asp_id",
        )
        labels = {"user_type": "Saisie en qualité de"}
        help_texts = {
            "nom": None,
            "numero": None,
            "voie": None,
            "lieu_dit": None,
            "code_postal": None,
            "commune": None,
            "contact_email": None,
            "site_internet": None,
            "telephone": None,
            "contact_url": None,
        }
        widgets = {
            "source": forms.HiddenInput(),
            "source_id": forms.HiddenInput(),
            "geom": forms.HiddenInput(),
            "nom": forms.TextInput(attrs={"placeholder": "ex: La ronde des fleurs"}),
            "numero": forms.TextInput(attrs={"placeholder": "ex: 4bis"}),
            "voie": forms.TextInput(attrs={"placeholder": "ex: rue des prés"}),
            "lieu_dit": forms.TextInput(attrs={"placeholder": "ex: le Val du Puits"}),
            "code_postal": forms.TextInput(attrs={"placeholder": "ex: 75001"}),
            "commune": forms.TextInput(attrs={"placeholder": "ex: Paris"}),
            "contact_email": forms.EmailInput(attrs={"placeholder": translate_lazy("ex: nom@domain.tld")}),
            "site_internet": forms.URLInput(attrs={"placeholder": "ex: http://etablissement.com"}),
            "telephone": forms.TextInput(attrs={"placeholder": "ex: 01.02.03.04.05"}),
            "contact_url": forms.URLInput(attrs={"placeholder": "https://mon-etablissement.fr/contactez-nous.html"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["activite"].required = True
        self.fields["nouvelle_activite"].required = False
        self.fields["activite"].help_text = "<a href='#' id='no_activite'>{}</a>".format(
            translate("Je ne trouve pas l'activité")
        )
        self.fields["source_id"].required = False

    def clean_nouvelle_activite(self):
        new_activity = self.cleaned_data["nouvelle_activite"]
        if not self.cleaned_data.get("activite"):
            return new_activity

        if self.cleaned_data["activite"].slug == "autre" and not new_activity:
            raise ValidationError(mark_safe(translate("Vous devez suggérer un nom d'activité pour l'établissement.")))
        return new_activity


class PublicErpAdminInfosForm(BasePublicErpInfosForm):
    ignore_duplicate_check = False

    def __init__(self, *args, **kwargs):
        self.ignore_duplicate_check = kwargs.pop("ignore_duplicate_check", False)
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.cleaned_data["geom"] is None or self.adresse_changed():
            self.geocode()

        if self.cleaned_data["lat"] and self.cleaned_data["lon"]:
            self.cleaned_data["geom"] = Point(float(self.cleaned_data["lon"]), float(self.cleaned_data["lat"]))

        # Unicity is made on activity + address
        activite = self.cleaned_data.get("activite")
        adresse = get_address_query_to_geocode(self.cleaned_data)
        if activite and adresse and not self.ignore_duplicate_check:
            existing = Erp.objects.find_duplicate(
                numero=self.cleaned_data.get("numero"),
                commune=self.cleaned_data.get("commune"),
                activite=self.cleaned_data.get("activite"),
                voie=self.cleaned_data.get("voie"),
                lieu_dit=self.cleaned_data.get("lieu_dit"),
            ).first()

            if existing:
                if existing.published:
                    erp_display = f'<a href="{existing.get_absolute_url()}">{activite} - {adresse}</a>'
                else:
                    erp_display = f"{activite} - {adresse}"
                raise ValidationError(
                    mark_safe(translate(f"L'établissement <b>{erp_display}</b> existe déjà dans la base de données."))
                )


class PublicErpDeleteForm(forms.Form):
    confirm = forms.BooleanField(
        label=translate_lazy("Supprimer cet établissement de la base de données (cette opération est irrémédiable)"),
        required=True,
    )

    def clean_confirm(self):
        confirm = self.cleaned_data["confirm"]
        if confirm is not True:
            raise ValidationError(translate("Vous devez confirmer la suppression pour la rendre effective."))
        return confirm


class PublicErpEditInfosForm(BasePublicErpInfosForm):
    def clean(self):
        # En édition publique d'un ERP, on ne met à jour la localisation que si
        # elle est absente ou que l'adresse a été modifiée
        if self.cleaned_data["geom"] != Point(
            float(self.cleaned_data.get("lon")),
            float(self.cleaned_data.get("lat")),
            srid=4326,
        ):
            self.cleaned_data["geom"] = Point(
                float(self.cleaned_data.get("lon")),
                float(self.cleaned_data.get("lat")),
                srid=4326,
            )

        if self.cleaned_data["geom"] is None or self.adresse_changed():
            self.geocode()


class ProviderGlobalSearchForm(forms.Form):
    lat = forms.DecimalField(required=False, widget=forms.HiddenInput)
    lon = forms.DecimalField(required=False, widget=forms.HiddenInput)
    code = forms.CharField(required=True, widget=forms.HiddenInput)
    what = forms.CharField(
        label=translate_lazy("Recherche"),
        help_text=mark_safe(
            translate_lazy(
                """Recherche sur le nom d'une administration publique, d'une entreprise, un
            <a href="https://www.service-public.fr/professionnels-entreprises/vosdroits/F32135" tabindex="-1" target="_blank">numéro SIRET</a>,
            l'adresse, l\'activité ou le
            <a href="https://www.insee.fr/fr/information/2406147" tabindex="-1" target="_blank">code NAF</a>."""
            )
        ),
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "ex. Mairie", "autocomplete": "off"}),
    )
    where = forms.CharField(
        label=translate_lazy("Commune"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": translate_lazy("Rechercher une commune"),
                "autocomplete": "off",
                "class": "autocomplete-input form-control",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        code = initial.get("code")
        if code:
            commune = Commune.objects.filter(code_insee=code).first()
            if commune:
                nom_departement = departements.DEPARTEMENTS[commune.departement]["nom"]
                commune_search = f"{commune.nom} ({commune.departement} - {nom_departement})"
                initial["commune_search"] = commune_search
                initial["code_insee"] = code
        super().__init__(*args, **kwargs)


class PublicAProposForm(forms.ModelForm):
    class Meta:
        model = Accessibilite
        fields = (
            "user_type",
            "registre_url",
            "conformite",
        )
        help_texts = schema.get_help_texts()

    user_type = forms.ChoiceField(
        label=translate_lazy("Vous êtes ?"),
        choices=[
            (
                Erp.USER_ROLE_PUBLIC,
                translate_lazy("Je suis simple contributeur"),
            ),
            (
                Erp.USER_ROLE_GESTIONNAIRE,
                translate_lazy("Je gère cet établissement"),
            ),
            (
                Erp.USER_ROLE_ADMIN,
                translate_lazy("Je représente la fonction publique"),
            ),
        ],
        widget=forms.RadioSelect(attrs={"class": "inline"}),
        required=True,
    )

    registre_url = forms.URLField(
        label=translate_lazy("Registre d'accessibilité"),
        help_text=schema.get_help_text("registre_url"),
        widget=forms.TextInput(attrs={"type": "url", "placeholder": "http://", "autocomplete": "off"}),
        required=False,
    )
    conformite = forms.ChoiceField(
        label=translate_lazy("Conformité"),
        help_text=schema.get_help_text("conformite"),
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "inline"}),
        required=False,
    )


class PublicPublicationForm(forms.ModelForm):
    class Meta:
        model = Erp
        fields = ("published",)
        help_texts = schema.get_help_texts()

    published = forms.BooleanField(
        label=translate_lazy("Je souhaite mettre en ligne cette fiche d'établissement immédiatement"),
        required=True,
        initial=True,
        widget=forms.CheckboxInput(attrs={"checked": "checked"}),
    )


class PublicClaimForm(forms.Form):
    ok = forms.BooleanField(
        required=True,
        label=translate_lazy("Je m'engage sur l'honneur à fournir des informations factuelles sur cet établissement."),
    )


FORM_FIELDS = {
    "user_type": {"label": PublicAProposForm.declared_fields["user_type"].label},
}


def get_label(field, default=""):
    try:
        return FORM_FIELDS[field].get("label", default)
    except KeyError:
        return default


def get_contrib_form_for_activity(activity: Activite):
    # FIXME enhance this, too hardcoded, find a better way to manage this + manage multiple groups
    group = activity.groups.first() if activity else None
    mapping = {"Hébergement": ContribAccessibiliteHotelsForm}
    if not group or group.name not in mapping:
        return ContribAccessibiliteForm
    else:
        return mapping[group.name]


def get_vote_button_title(is_authenticated, is_user_erp_owner, has_vote, default):
    if not is_authenticated:
        return "Vous devez vous connecter pour voter"
    if is_user_erp_owner:
        return "Vous ne pouvez pas voter sur votre établissement"
    if has_vote:
        return "Retirer mon vote"
    return default
