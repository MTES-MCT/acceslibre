from copy import copy

from django import forms
from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError
from django.db.models import F
from django.forms import modelform_factory, widgets
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as translate
from django.utils.translation import gettext_lazy as translate_lazy
from magic_profanity import ProfanityFilter

from compte.models import UserStats
from erp import schema
from erp.imports.utils import get_address_query_to_geocode
from erp.models import ACTIVITY_GROUPS, Accessibilite, Activite, Commune, Erp
from erp.provider import departements, geocoder

from .fields import ActivityField
from .schema import get_conditional_fields_in, get_conditional_fields_not_in


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
        exclude = ["pk", "completion_rate"] + schema.get_conditional_fields()
        widgets = get_widgets_for_accessibilite()
        labels = schema.get_labels()
        help_texts = schema.get_help_texts()
        required = schema.get_required_fields()

    def __init__(self, *args, **kwargs):
        self._user = kwargs.pop("user", False)
        super().__init__(*args, **kwargs)

    def clean_entree_dispositif_appel_type(self):
        if "entree_dispositif_appel" in self.cleaned_data and self.cleaned_data["entree_dispositif_appel"] is not True:
            return None
        return self.cleaned_data["entree_dispositif_appel_type"]

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

    def clean_profanity(self):
        profanity_filter = ProfanityFilter()
        profanity_filter.load_words_from_file(settings.FRENCH_PROFANITY_WORDLIST)

        for free_text in schema.get_free_text_fields():
            field_value = getattr(self.instance, free_text, None)
            if not field_value:
                continue

            if profanity_filter.has_profanity(field_value):
                old_value = Accessibilite.objects.filter(pk=self.instance.pk).values_list(free_text, flat=True).first()
                setattr(self.instance, free_text, old_value)

                if self._user:
                    user_stats, _ = UserStats.objects.get_or_create(user=self._user)
                    user_stats.nb_profanities = F("nb_profanities") + 1
                    user_stats.save(update_fields=("nb_profanities",))

    def save(self, commit=True):
        self.clean_profanity()
        instance = super().save(commit=False)

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class ContribAccessibiliteHotelsForm(ContribAccessibiliteForm):
    fields_to_remove = ("accueil_audiodescription_presence", "accueil_audiodescription")
    conditionals_to_add = get_conditional_fields_in("hosting")
    conditionals_to_remove = get_conditional_fields_not_in("hosting")

    class Meta:
        model = Accessibilite
        exclude = ("pk",)
        widgets = get_widgets_for_accessibilite()
        labels = schema.get_labels(include_conditional=["hosting"])
        help_texts = schema.get_help_texts(include_conditional=["hosting"])
        required = schema.get_required_fields()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in copy(self.fields):
            if field not in schema.get_help_texts(include_conditional="hosting").keys():
                self.fields.pop(field, None)


class ContribAccessibiliteSchoolsForm(ContribAccessibiliteForm):
    accueil_espaces_ouverts = forms.MultipleChoiceField(
        required=False,
        choices=schema.get_field_choices("accueil_espaces_ouverts"),
        widget=forms.CheckboxSelectMultiple,
        label=schema.get_label("accueil_espaces_ouverts"),
        help_text=schema.get_help_text("accueil_espaces_ouverts"),
    )
    fields_to_remove = ("labels", "labels_familles_handicap", "labels_autre")
    conditionals_to_add = get_conditional_fields_in("school")
    conditionals_to_remove = get_conditional_fields_not_in("school")

    class Meta:
        model = Accessibilite
        exclude = ("pk",)
        widgets = get_widgets_for_accessibilite()
        labels = schema.get_labels(include_conditional=["school"])
        help_texts = schema.get_help_texts(include_conditional=["school"])
        required = schema.get_required_fields()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in copy(self.fields):
            if field not in schema.get_help_texts(include_conditional="school").keys():
                self.fields.pop(field, None)


class ContribAccessibiliteFloorsForm(ContribAccessibiliteForm):
    fields_to_remove = []
    conditionals_to_add = get_conditional_fields_in("floor")
    conditionals_to_remove = get_conditional_fields_not_in("floor")

    class Meta:
        model = Accessibilite
        exclude = ("pk",)
        widgets = get_widgets_for_accessibilite()
        labels = schema.get_labels(include_conditional=["floor"])
        help_texts = schema.get_help_texts(include_conditional=["floor"])
        required = schema.get_required_fields()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in copy(self.fields):
            if field not in schema.get_help_texts(include_conditional="floor").keys():
                self.fields.pop(field, None)


class AdminAccessibiliteForm(ContribAccessibiliteForm):
    # Note: defining `labels` and `help_texts` in `Meta` doesn't work with custom
    # fields, hence why we set them up manually for each fields.
    class Meta:
        model = Accessibilite
        exclude = ["pk"]
        widgets = get_widgets_for_accessibilite()
        labels = schema.get_labels(include_conditional=["hosting", "school", "floor"])
        help_texts = schema.get_help_texts(include_conditional=["hosting", "school", "floor"])
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
    naf_ape_code = SimpleArrayField(
        forms.CharField(),
        label=translate_lazy("Code NAF/APE"),
        widget=widgets.Textarea(),
        delimiter="\n",
        required=True,
        help_text=translate_lazy("Un code APE/NAF par ligne"),
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
                or self.cleaned_data.get("ban_id") != self.instance.ban_id
            )
        except KeyError:
            return True

    def format_error(self, message):
        contact_bug_url = reverse("contact_topic", kwargs={"topic": "bug"})
        return format_html(
            "{}. "
            + translate('Veuillez vérifier votre saisie ou <a href="{}" target="_blank">signaler une erreur</a>.'),
            message,
            contact_bug_url,
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

        # NOTE: ATM there is a bug on api-adresse, it does not return postal_code for TOM
        # ex https://api-adresse.data.gouv.fr/search/?q=41+Avenue+FOCH%2C+NOUMEA&limit=1
        # Once solved on their side, remove the following if block
        if code_postal and not locdata["code_postal"] and locdata["code_insee"]:
            if code_postal[:2] == locdata["code_insee"][:2]:
                locdata["code_postal"] = code_postal

        # Ensure picking the right postcode
        if code_postal and locdata["code_postal"] and code_postal != locdata["code_postal"]:
            dpt_result = locdata["code_postal"][:2]
            if departement != dpt_result:
                # Different departement, too risky to consider it valid; raise an error
                self.raise_validation_error(
                    "code_postal",
                    format_html(
                        translate("Cette adresse n'est pas localisable au code postal {} (mais l'est au code {})"),
                        code_postal,
                        locdata["code_postal"],
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
        self.cleaned_data["ban_id"] = locdata.get("ban_id")


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


class BasePublicErpInfosForm(BaseErpForm):
    lat = forms.DecimalField(widget=forms.HiddenInput)
    lon = forms.DecimalField(widget=forms.HiddenInput)
    nouvelle_activite = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={
                "class": "fr-input hidden",
                "id": "new_activity",
                "aria-describedby": "nouvelle-activite-error-message",
            }
        ),
    )
    asp_id = forms.CharField(widget=forms.HiddenInput, required=False)
    user_type = forms.CharField(initial=Erp.USER_ROLE_PUBLIC, widget=forms.HiddenInput, required=False)

    class Meta:
        model = Erp
        fields = (
            "source",
            "source_id",
            "asp_id",
            "geom",
            "nom",
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
            "user_type",
            "ban_id",
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
            "nom": forms.TextInput(
                attrs={
                    "placeholder": "ex: La ronde des fleurs",
                    "class": "fr-input",
                    "aria-describedby": "nom-error-message",
                }
            ),
            "numero": forms.TextInput(attrs={"placeholder": "ex: 4bis", "class": "fr-input"}),
            "voie": forms.TextInput(
                attrs={"placeholder": "ex: rue des prés", "class": "fr-input", "aria-describedby": "voie-error-message"}
            ),
            "lieu_dit": forms.TextInput(
                attrs={
                    "placeholder": "ex: le Val du Puits",
                    "class": "fr-input",
                    "aria-describedby": "lieu-dit-error-message",
                }
            ),
            "code_postal": forms.TextInput(
                attrs={"placeholder": "ex: 75001", "class": "fr-input", "aria-describedby": "code-postal-error-message"}
            ),
            "commune": forms.TextInput(
                attrs={"placeholder": "ex: Paris", "class": "fr-input", "aria-describedby": "commune-error-message"}
            ),
            "contact_email": forms.EmailInput(attrs={"class": "fr-input"}),
            "site_internet": forms.URLInput(attrs={"class": "fr-input"}),
            "telephone": forms.TextInput(attrs={"class": "fr-input"}),
            "contact_url": forms.URLInput(attrs={"class": "fr-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get("instance")
        initial = kwargs.get("initial")
        if instance and instance.activite:
            self.fields["activite"] = ActivityField(initial=instance.activite)
            if instance.has_miscellaneous_activity:
                self.fields["nouvelle_activite"].widget = forms.TextInput(
                    attrs={"id": "new_activity", "class": "fr-input hidden"}
                )
        elif initial:
            self.fields["activite"] = ActivityField(initial=initial.get("activite_slug"))
            if initial.get("activite_slug") == Activite.SLUG_MISCELLANEOUS and initial.get("new_activity"):
                self.fields["nouvelle_activite"].initial = initial.get("new_activity")
                self.fields["nouvelle_activite"].widget = forms.TextInput(
                    attrs={"id": "new_activity", "class": "fr-input hidden"}
                )
        else:
            self.fields["activite"] = ActivityField()

        self.fields["nouvelle_activite"].required = False
        self.fields["source_id"].required = False

    def clean_nouvelle_activite(self):
        new_activity = self.cleaned_data["nouvelle_activite"]
        if not self.cleaned_data.get("activite"):
            return new_activity

        if self.cleaned_data["activite"].slug == "autre" and not new_activity:
            raise ValidationError(translate("Vous devez suggérer un nom d'activité pour l'établissement."))
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
            existing_erps = Erp.objects.find_duplicate(
                numero=self.cleaned_data.get("numero"),
                commune=self.cleaned_data.get("commune"),
                activite=self.cleaned_data.get("activite"),
                voie=self.cleaned_data.get("voie"),
                lieu_dit=self.cleaned_data.get("lieu_dit"),
            )

            if any([erp.permanently_closed for erp in existing_erps]):
                url_contact = reverse("contact_topic", kwargs={"topic": "deletion"})
                raise ValidationError(
                    mark_safe(
                        translate(
                            "Cet établissement ne peut être créé car il a été signalé comme définitivement fermé. <a href='%(url_contact)s'>Contactez l'équipe accèslibre</a> s'il s'agit d’une erreur."
                            % ({"url_contact": url_contact})
                        )
                    )
                )

            existing = existing_erps.published().first()

            if existing:
                if existing.published:
                    erp_display = format_html(
                        '<a href="{}" target="_blank" class="fr-link">{} - {}</a>',
                        existing.get_absolute_url(),
                        activite,
                        adresse,
                    )
                else:
                    erp_display = format_html("{} - {}", activite, adresse)

                raise ValidationError(
                    format_html(
                        translate("L'établissement <b>{}</b> existe déjà dans la base de données."),
                        erp_display,
                    )
                )


class PublicErpDeleteForm(forms.Form):
    confirm = forms.BooleanField(
        label=translate_lazy("Supprimer cet établissement de la base de données (cette opération est irrémédiable)"),
        widget=forms.CheckboxInput(attrs={"class": "fr-checkbox"}),
        required=True,
    )

    def clean_confirm(self):
        confirm = self.cleaned_data["confirm"]
        if confirm is not True:
            raise ValidationError(translate("Vous devez confirmer la suppression pour la rendre effective."))
        return confirm


class PublicErpEditInfosForm(BasePublicErpInfosForm):
    def clean(self):
        if not self.cleaned_data.get("lon") or not self.cleaned_data.get("lat"):
            raise ValidationError(translate("Cet ERP est non localisable."))
        # En édition publique d'un ERP, on ne met à jour la localisation que si
        # elle est absente ou que l'adresse a été modifiée
        point_changed = False
        if self.cleaned_data["geom"] != Point(
            float(self.cleaned_data.get("lon")),
            float(self.cleaned_data.get("lat")),
            srid=4326,
        ):
            point_changed = True

        if self.cleaned_data["geom"] is None or self.adresse_changed():
            self.geocode()

        if point_changed:
            self.cleaned_data["geom"] = Point(
                float(self.cleaned_data.get("lon")),
                float(self.cleaned_data.get("lat")),
                srid=4326,
            )


class ProviderGlobalSearchForm(forms.Form):
    new_activity = forms.CharField(required=False, widget=forms.HiddenInput)
    activity_slug = forms.CharField(required=False)
    lat = forms.DecimalField(required=False, widget=forms.HiddenInput)
    lon = forms.DecimalField(required=False, widget=forms.HiddenInput)
    code = forms.CharField(required=True, widget=forms.HiddenInput)
    postcode = forms.CharField(required=False, widget=forms.HiddenInput)
    what = forms.CharField(
        help_text=mark_safe(
            translate_lazy(
                """Recherche sur le nom d'une administration publique, d'une entreprise, un
            <a href="https://www.service-public.fr/professionnels-entreprises/vosdroits/F32135" tabindex="-1" target="_blank">numéro SIRET</a>,
            l'adresse, l\'activité ou le
            <a href="https://www.insee.fr/fr/information/2406147" tabindex="-1" target="_blank">code NAF</a>."""
            )
        ),
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "ex. Mairie", "autocomplete": "off"}),
    )
    where = forms.CharField(
        label=translate_lazy("Commune"),
        required=False,
        widget=forms.TextInput(
            attrs={
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
        self.fields["activite"] = ActivityField(required=False)

    def clean_postcode(self):
        postcodes = self.cleaned_data["postcode"].split(",")
        if len(postcodes) == 1:
            return self.cleaned_data["postcode"]
        return postcodes[0][0:2] + "000"

    def clean(self):
        cleaned_data = super().clean()

        what = cleaned_data.get("what")
        cleaned_data["activite"] = cleaned_data.get("activite") or ""
        activite = cleaned_data.get("activite")

        if not what and not activite:
            self.add_error("what", translate("Vous devez préciser une activité ou un nom d'établissement."))

        if (
            cleaned_data.get("where")
            or (cleaned_data.get("lat") and cleaned_data.get("lon"))
            or cleaned_data.get("code")
        ):
            return cleaned_data
        self.add_error("where", translate("Veuillez renseigner une adresse."))
        return cleaned_data


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
        widget=forms.TextInput(attrs={"type": "url", "autocomplete": "off"}),
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


FORM_FIELDS = {
    "user_type": {"label": PublicAProposForm.declared_fields["user_type"].label},
}


def get_label(field, default=""):
    try:
        return FORM_FIELDS[field].get("label", default)
    except KeyError:
        return default


def get_contrib_forms_for_activity(activity: Activite):
    if not activity:
        return [ContribAccessibiliteForm]

    # FIXME enhance this, too hardcoded, find a better way to manage this
    mapping = {
        ACTIVITY_GROUPS["HOSTING"]: ContribAccessibiliteHotelsForm,
        ACTIVITY_GROUPS["SCHOOL"]: ContribAccessibiliteSchoolsForm,
        ACTIVITY_GROUPS["FLOOR"]: ContribAccessibiliteFloorsForm,
    }

    groups = activity.groups.all()
    forms = [ContribAccessibiliteForm]

    for group in groups:
        form_class = mapping.get(group.name, ContribAccessibiliteForm)
        forms.append(form_class)

    return forms


class CombinedAccessibiliteForm(forms.Form):
    def __init__(self, forms_list, form_fields, *args, **kwargs):
        self.form_classes = forms_list
        self.form_fields = form_fields
        self.accessibilite_instance = kwargs.pop("instance", None)
        self.user = kwargs.pop("user", None)

        instance_data = {
            field: getattr(self.accessibilite_instance, field)
            for field in form_fields
            if self.accessibilite_instance and hasattr(self.accessibilite_instance, field)
        }

        if self.accessibilite_instance:
            kwargs["initial"] = {**instance_data, **kwargs.get("initial", {})}

        super().__init__(*args, **kwargs)

        self.sub_forms = []
        fields_to_remove = set()

        for form_class in forms_list:
            to_remove = getattr(form_class, "fields_to_remove", ())
            fields_to_remove |= set(to_remove or ())

        for form_class in forms_list:
            Form = modelform_factory(Accessibilite, form=form_class, fields=form_fields)
            form_instance = Form(
                *(args or ()),
                instance=self.accessibilite_instance,
                user=self.user,
                initial=self.initial or None,
            )
            self.sub_forms.append(form_instance)

            for name, field in form_instance.fields.items():
                self.fields[name] = field

        for field in fields_to_remove:
            self.fields.pop(field, None)

    def is_valid(self):
        combined_valid = super().is_valid()

        if combined_valid:
            for form in self.sub_forms:
                form.data = self.data
                form.full_clean()

        sub_forms_valid = all(form.is_valid() for form in self.sub_forms)

        return combined_valid and sub_forms_valid

    def save(self, commit=True):
        if not self.sub_forms:
            return None

        instance = self.accessibilite_instance or Accessibilite()

        for form in self.sub_forms:
            temp_instance = form.save(commit=False)
            for field_name in form.cleaned_data.keys():
                setattr(instance, field_name, getattr(temp_instance, field_name))

        if commit:
            instance.save()
            self.instance = instance
            self.save_m2m()
        else:
            self.instance = instance

        return self.instance

    def save_m2m(self):
        if not getattr(self, "instance", None):
            return

        for form in self.sub_forms:
            form.instance = self.instance
            if hasattr(form, "save_m2m"):
                form.save_m2m()
