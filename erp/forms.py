from django import forms
from django.contrib.auth.models import User
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError
from django.forms import widgets
from django.utils.safestring import mark_safe
from django_registration.forms import RegistrationFormUniqueEmail
from . import schema
from . import geocoder
from . import sirene
from .models import (
    Activite,
    Accessibilite,
    Commune,
    Erp,
    Label,
)


def bool_radios():
    return forms.RadioSelect(attrs={"class": "inline"})


def get_widgets_for_accessibilite():
    field_names = schema.get_nullable_bool_fields()
    return dict([(f, bool_radios()) for f in field_names])


class CustomRegistrationForm(RegistrationFormUniqueEmail):
    class Meta(RegistrationFormUniqueEmail.Meta):
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        ]


class AdminAccessibiliteForm(forms.ModelForm):
    accueil_equipements_malentendants = forms.MultipleChoiceField(
        required=False,
        choices=schema.EQUIPEMENT_MALENTENDANT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        # Note: defining `labels` and `help_texts` in `Meta` doesn't work with custom fields...
        label="Équipement(s) sourd/malentendant",  # FIXME: use get_label
        help_text=schema.get_help_text("accueil_equipements_malentendants"),
    )
    labels_familles_handicap = forms.MultipleChoiceField(
        required=False,
        choices=schema.HANDICAP_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        # Note: defining `labels` and `help_texts` in `Meta` doesn't work with custom fields...
        label="Famille(s) de handicap concernées(s)",  # FIXME: use get_label
        help_text=schema.get_help_text("labels_familles_handicap"),
    )
    labels = forms.ModelMultipleChoiceField(
        label="Labels d'accessibilité",
        help_text=schema.get_help_text("labels"),
        queryset=Label.objects,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Accessibilite
        exclude = ("pk",)
        widgets = get_widgets_for_accessibilite()
        labels = schema.get_labels()
        help_texts = schema.get_help_texts()


class AdminActiviteForm(forms.ModelForm):
    class Meta:
        model = Activite
        exclude = ("pk",)

    mots_cles = SimpleArrayField(
        forms.CharField(),
        widget=widgets.Textarea(),
        delimiter="\n",
        required=False,
        help_text="Un mots-clé par ligne",
    )


class AdminCommuneForm(forms.ModelForm):
    class Meta:
        model = Commune
        exclude = ("pk",)

    code_postaux = SimpleArrayField(
        forms.CharField(),
        widget=widgets.Textarea(),
        delimiter="\n",
        required=False,
        help_text="Un code postal par ligne",
    )


class BaseErpForm(forms.ModelForm):
    def __init__(self, *args, geocode=None, **kwargs):
        self.do_geocode = geocode if geocode else geocoder.geocode
        super().__init__(*args, **kwargs)

    def get_adresse(self):
        parts = [
            self.cleaned_data[f]
            for f in ["numero", "voie", "lieu_dit", "code_postal", "commune",]
            if f in self.cleaned_data and self.cleaned_data[f] is not None
        ]
        return " ".join(parts).strip()

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

    def geocode(self):
        adresse = self.get_adresse()
        locdata = self.do_geocode(adresse)
        if not locdata or locdata.get("geom") is None:
            raise ValidationError(
                {
                    "voie": f"Adresse non localisable : {adresse}. "
                    "Veuillez vérifier votre saisie ou contactez un administrateur."
                }
            )
        self.cleaned_data["geom"] = locdata["geom"]
        self.cleaned_data["numero"] = locdata["numero"]
        self.cleaned_data["voie"] = locdata["voie"]
        self.cleaned_data["lieu_dit"] = locdata["lieu_dit"]
        self.cleaned_data["code_postal"] = locdata["code_postal"]
        self.cleaned_data["commune"] = locdata["commune"]
        self.cleaned_data["code_insee"] = locdata["code_insee"]


class AdminErpForm(BaseErpForm):
    class Meta:
        model = Erp
        exclude = (
            "pk",
            "user",
            "search_vector",
            "source",
            "source_id",
        )

    photon_autocomplete = forms.CharField(
        max_length=255,
        required=False,
        label="Recherche d'un ERP",
        widget=forms.TextInput(attrs={"type": "search", "class": "vTextField"}),
        help_text='Recherchez un ERP par sa raison sociale et son adresse. Ex: "Intermarché Lyon".',
    )

    ban_autocomplete = forms.CharField(
        max_length=255,
        required=False,
        label="Recherche de l'adresse",
        widget=forms.TextInput(attrs={"type": "search", "class": "vTextField"}),
        help_text="Entrez l'adresse de l'ERP et sélectionnez la suggestion correspondante dans la liste.",
    )

    def clean(self):
        if self.cleaned_data["geom"] is None or self.adresse_changed():
            self.geocode()


class ViewAccessibiliteForm(forms.ModelForm):
    "This form is used to render Accessibilite data in Erp details pages."

    class Meta:
        model = Accessibilite
        exclude = ("pk", "erp", "labels")

    fieldsets = schema.get_form_fieldsets(exclude_sections=[schema.SECTION_LABELS])

    def get_accessibilite_data(self):
        data = {}
        for section, section_info in self.fieldsets.items():
            data[section] = {
                "icon": section_info["icon"],
                "tabid": section_info["tabid"],
                "description": section_info["description"],
                "fields": [],
            }
            section_fields = section_info["fields"]
            for field_data in section_fields:
                field = self[field_data["id"]]
                field_value = field.value()
                if field_value == []:
                    field_value = None
                warning = None
                if "warn_if" in field_data and field_data["warn_if"] is not None:
                    if callable(field_data["warn_if"]):
                        warning = field_data["warn_if"](field_value, self.instance)
                    else:
                        warning = field_value == field_data["warn_if"]
                data[section]["fields"].append(
                    {
                        "template_name": field.field.widget.template_name,
                        "name": field.name,
                        "label": field.label,
                        "help_text": schema.get_help_text(field.name, field.help_text),
                        "value": field_value,
                        "warning": warning,
                    }
                )
            # Discard empty sections to avoid rendering empty menu items
            empty_section = all(
                self[f["id"]].value() in [None, "", []] for f in section_fields
            )
            if empty_section:
                data.pop(section)
        return data


class BasePublicErpInfosForm(BaseErpForm):
    class Meta:
        model = Erp
        fields = (
            "nom",
            "activite",
            "numero",
            "voie",
            "lieu_dit",
            "code_postal",
            "commune",
            "siret",
            "geom",
            "contact_email",
            "site_internet",
            "telephone",
        )
        labels = {"siret": "Numéro SIRET", "user_type": "Saisie en qualité de"}
        help_texts = {
            "lieu_dit": "Lieu-dit ou complément d'adresse",
            "siret": mark_safe(
                'Le numéro <a href="https://fr.wikipedia.org/wiki/SIRET" '
                'target="_blank">SIRET</a> à 14 chiffres de l\'établissement, '
                "si l'établissement en dispose."
            ),
            "voie": "Le type et le nom de la voie, par exemple: rue Charles Péguy, ou place Jean Jaurès",
        }
        widgets = {
            "nom": forms.TextInput(attrs={"placeholder": "ex: La ronde des fleurs"}),
            "numero": forms.TextInput(attrs={"placeholder": "ex: 4bis"}),
            "voie": forms.TextInput(attrs={"placeholder": "ex: rue des prés"}),
            "lieu_dit": forms.TextInput(attrs={"placeholder": "ex: le Val du Puits"}),
            "code_postal": forms.TextInput(attrs={"placeholder": "ex: 75001"}),
            "commune": forms.TextInput(attrs={"placeholder": "ex: Paris"}),
            "siret": forms.TextInput(attrs={"placeholder": "ex: 88076068100010"}),
            "contact_email": forms.EmailInput(
                attrs={"placeholder": "ex: nom@domain.tld"}
            ),
            "site_internet": forms.URLInput(
                attrs={"placeholder": "ex: http://etablissement.com"}
            ),
            "telephone": forms.TextInput(attrs={"placeholder": "ex: 01.02.03.04.05"}),
        }

    recevant_du_public = forms.BooleanField(
        label="Cet établissement reçoit du public",
        help_text=mark_safe(
            'Seuls les <a href="https://www.service-public.fr/professionnels-entreprises/vosdroits/F32351" target="_blank">'
            "établissements recevant du public</a> peuvent être ajoutés à cette base de données."
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Les contributions publiques rendent obligatoire le renseignement de l'activité
        self.fields["activite"].required = True
        self.fields["activite"].help_text = "Domaine d'activité de l'établissement"


class PublicErpAdminInfosForm(BasePublicErpInfosForm):
    def clean(self):
        # geom
        self.geocode()

        # Unicité du numéro SIRET
        # FIXME: should be enforced in model
        siret = self.cleaned_data["siret"]
        if siret and Erp.objects.exists_by_siret(siret):
            raise ValidationError(
                {
                    "siret": f"Un établissement disposant du numéro SIRET {siret} "
                    "existe déjà dans la base de données."
                }
            )
        # Unicité du nom et de l'adresse
        nom = self.cleaned_data.get("nom")
        adresse = self.get_adresse()
        exists = Erp.objects.exists_by_name_adresse(
            nom__iexact=self.cleaned_data.get("nom"),
            voie__iexact=self.cleaned_data.get("voie"),
            lieu_dit__iexact=self.cleaned_data.get("lieu_dit"),
            code_postal__iexact=self.cleaned_data.get("code_postal"),
            commune__iexact=self.cleaned_data.get("commune"),
        )
        if exists > 0:
            raise ValidationError(
                mark_safe(
                    f"L'établissement <b>{nom} - {adresse}</b> "
                    "existe déjà dans la base de données."
                )
            )


class PublicErpEditInfosForm(BasePublicErpInfosForm):
    def clean(self):
        # En édition publique d'un ERP, on ne met à jour la localisation que si
        # elle est absente ou que l'adresse a été modifiée
        if self.cleaned_data["geom"] is None or self.adresse_changed():
            self.geocode()


class PublicLocalisationForm(forms.Form):
    lat = forms.DecimalField(widget=forms.HiddenInput)
    lon = forms.DecimalField(widget=forms.HiddenInput)

    def clean(self):
        try:
            self.cleaned_data["lat"] = float(self.cleaned_data["lat"])
            self.cleaned_data["lon"] = float(self.cleaned_data["lon"])
        except (TypeError, ValueError):
            raise ValidationError("Données de localisation invalides.")


class PublicEtablissementSearchForm(forms.Form):
    nom = forms.CharField(
        label="Nom de l'établissement",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "ex. Bistro Brooklyn"}),
    )
    lieu = forms.CharField(
        label="Code postal ou nom de la commune",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "ex. 75010 ou Paris"}),
    )


class PublicSiretSearchForm(forms.Form):
    siret = forms.CharField(
        label="Numéro SIRET",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "ex. 88076068100010"}),
    )

    def clean_siret(self):
        siret = sirene.validate_siret(self.cleaned_data["siret"])
        if not siret:
            raise ValidationError(
                "Ce numéro SIRET est invalide, veuillez vérifier le format."
            )
        self.cleaned_data["siret"] = siret
        return siret

    def clean(self):
        siret = self.cleaned_data.get("siret")
        if siret and Erp.objects.exists_by_siret(siret):
            raise ValidationError(
                {
                    "siret": f"Un établissement disposant du numéro SIRET {siret} "
                    "existe déjà dans la base de données."
                }
            )


class PublicPublicationForm(forms.ModelForm):
    class Meta:
        model = Erp
        fields = ("user_type",)

    user_type = forms.ChoiceField(
        label="Mon profil",
        choices=[
            (Erp.USER_ROLE_PUBLIC, "Je fréquente cet établissement",),
            (Erp.USER_ROLE_GESTIONNAIRE, "Je gère cet établissement",),
            (Erp.USER_ROLE_ADMIN, "Je représente une administration publique",),
        ],
        widget=forms.RadioSelect(attrs={"class": "inline"}),
    )
    certif = forms.BooleanField(
        label="Je certifie sur l'honneur l'exactitude de ces informations et consens à leur publication sur Access4all.",
        required=True,
    )

    def clean_certif(self):
        if not self.cleaned_data.get("certif", False):
            raise ValidationError(
                "Publication impossible sans ces garanties de votre part"
            )
        return True
