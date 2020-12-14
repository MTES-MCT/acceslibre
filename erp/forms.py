import requests

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.forms import widgets
from django.urls import reverse
from django.utils.safestring import mark_safe


from django_registration.forms import RegistrationFormUniqueEmail
from requests.exceptions import RequestException

from erp import schema
from erp.models import (
    Activite,
    Accessibilite,
    Commune,
    Erp,
)
from erp.provider import departements, geocoder


USERNAME_RULES = """
Uniquement des lettres, nombres et les caractères « . », « - » et « _ ».
<strong>Note&nbsp;: ce nom d'utilisateur pourra être affiché publiquement sur le site si vous contribuez.</strong>
"""


def bool_radios():
    return forms.RadioSelect(attrs={"class": "inline"})


def get_widgets_for_accessibilite():
    field_names = schema.get_nullable_bool_fields()
    return dict([(f, bool_radios()) for f in field_names])


def define_username_field():
    return forms.CharField(
        max_length=32,
        help_text=f"Requis. 32 caractères maximum. {USERNAME_RULES}",
        required=True,
        label="Nom d’utilisateur",
        validators=[RegexValidator(r"^[\w.-]+\Z", message=USERNAME_RULES)],
    )


class CustomRegistrationForm(RegistrationFormUniqueEmail):
    class Meta(RegistrationFormUniqueEmail.Meta):
        model = get_user_model()
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
            "next",
        ]

    username = define_username_field()
    next = forms.CharField(required=False)


class UsernameChangeForm(forms.Form):
    username = define_username_field()

    def clean_username(self):
        username = self.cleaned_data["username"]
        if get_user_model().objects.filter(username__iexact=username).count() > 0:
            raise ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username


class AdminAccessibiliteForm(forms.ModelForm):
    # Note: defining `labels` and `help_texts` in `Meta` doesn't work with custom
    # fields, hence why we set them up manually for each fields.

    class Meta:
        model = Accessibilite
        exclude = ("pk",)
        widgets = get_widgets_for_accessibilite()
        labels = schema.get_labels()
        help_texts = schema.get_help_texts()

    accueil_equipements_malentendants = forms.MultipleChoiceField(
        required=False,
        choices=schema.EQUIPEMENT_MALENTENDANT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label=schema.get_label("accueil_equipements_malentendants"),
        help_text=schema.get_help_text("accueil_equipements_malentendants"),
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
    sanitaires_adaptes = forms.ChoiceField(
        required=False,
        label=schema.get_label("sanitaires_adaptes"),
        help_text=schema.get_help_text("sanitaires_adaptes"),
        choices=schema.NULLABLE_BOOL_NUM_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "inline"}),
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        obj = kwargs.get("instance")
        if obj and obj.sanitaires_adaptes is not None and obj.sanitaires_adaptes > 1:
            initial["sanitaires_adaptes"] = 1
            kwargs["initial"] = initial

        super().__init__(*args, **kwargs)

    def clean_sanitaires_adaptes(self):
        # Specific case where we want to map nullable bool choices
        # to 0 and 1 integers, hence why we use NULLABLE_BOOL_NUM_CHOICES
        # as choices.
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

    def get_adresse_query(self):
        parts = [
            self.cleaned_data.get("numero") or "",
            self.cleaned_data.get("voie") or "",
        ]
        voie_ville = " ".join([p for p in parts if p != ""]).strip()
        adresse_parts = [
            voie_ville,
            self.cleaned_data.get("lieu_dit") or "",
            self.cleaned_data.get("commune") or "",
        ]
        return ", ".join([p for p in adresse_parts if p != ""])

    def format_error(self, message):
        signalement_url = reverse("contact_topic", kwargs={"topic": "support"})
        return mark_safe(
            f'{message}. Veuillez vérifier votre saisie ou <a href="{signalement_url}" target="_blank">signaler une erreur</a>.'
        )

    def raise_validation_error(self, field, message):
        raise ValidationError({field: self.format_error(message)})

    def geocode(self):
        adresse = self.get_adresse_query()
        code_postal = self.cleaned_data.get("code_postal", "").strip() or None
        departement = code_postal[:2] if code_postal and len(code_postal) == 5 else None
        commune_input = self.cleaned_data.get("commune")
        commune = Commune.objects.search_by_nom_code_postal(
            commune_input, code_postal
        ).first()
        locdata = None
        try:
            locdata = self.do_geocode(
                adresse, citycode=commune.code_insee if commune else None
            )
        except RuntimeError as err:
            raise ValidationError(err)

        # Check for geocoded results
        if not locdata or locdata.get("geom") is None:
            self.raise_validation_error(
                "voie", f"Adresse non localisable : {adresse} ({code_postal})"
            )

        # Ensure picking the right postcode
        if (
            code_postal
            and locdata["code_postal"]
            and code_postal != locdata["code_postal"]
        ):
            dpt_result = locdata["code_postal"][:2]
            if departement != dpt_result:
                # Different departement, too risky to consider it valid; raise an error
                self.raise_validation_error(
                    "code_postal",
                    mark_safe(
                        "Cette adresse n'est pas localisable au code postal "
                        f"{code_postal} (mais l'est au code {locdata['code_postal']})"
                    ),
                )

        # Validate code insee
        if (
            self.cleaned_data.get("code_insee")
            and self.cleaned_data["code_insee"] != locdata["code_insee"]
        ):
            self.raise_validation_error(
                "code_insee",
                f"Cette adresse n'est pas localisable au code INSEE {self.cleaned_data['code_insee']}",
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


class AdminErpForm(BaseErpForm):
    class Meta:
        model = Erp
        exclude = (
            "pk",
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
        exclude = ("pk", "erp")

    fieldsets = schema.get_form_fieldsets()

    def get_accessibilite_data(self):
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
                        "label": schema.get_label(field.name, field.label),
                        "help_text_ui": schema.get_help_text_ui(field.name),
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
            "source",
            "source_id",
            "geom",
            "nom",
            "activite",
            "numero",
            "voie",
            "lieu_dit",
            "code_postal",
            "commune",
            "siret",
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
            "source": forms.HiddenInput(),
            "source_id": forms.HiddenInput(),
            "geom": forms.HiddenInput(),
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
        # Source id non requis
        self.fields["source_id"].required = False


class PublicErpAdminInfosForm(BasePublicErpInfosForm):
    def clean(self):
        # geom
        if not self.cleaned_data["geom"]:
            self.geocode()

        # Unicité du numéro SIRET
        siret = self.cleaned_data["siret"]
        if siret and Erp.objects.find_by_siret(siret):
            raise ValidationError(
                {
                    "siret": f"Un établissement disposant du numéro SIRET {siret} existe déjà dans la base de données."
                }
            )
        # Unicité du nom et de l'adresse
        nom = self.cleaned_data.get("nom")
        adresse = self.get_adresse_query()
        existing = Erp.objects.filter(
            nom__iexact=self.cleaned_data.get("nom"),
            voie__iexact=self.cleaned_data.get("voie"),
            lieu_dit__iexact=self.cleaned_data.get("lieu_dit"),
            code_postal__iexact=self.cleaned_data.get("code_postal"),
            commune__iexact=self.cleaned_data.get("commune"),
        ).first()
        if existing:
            if existing.is_online():
                erp_display = (
                    f'<a href="{existing.get_absolute_url()}">{nom} - {adresse}</a>'
                )
            else:
                erp_display = f"{nom} - {adresse}"
            raise ValidationError(
                mark_safe(
                    f"L'établissement <b>{erp_display}</b> existe déjà dans la base de données."
                )
            )


class PublicErpDeleteForm(forms.Form):
    confirm = forms.BooleanField(
        label="Supprimer cet établissement de la base de données (cette opération est irrémédiable)",
        required=True,
    )

    def clean_confirm(self):
        confirm = self.cleaned_data["confirm"]
        if confirm is not True:
            raise ValidationError(
                "Vous devez confirmer la suppression pour la rendre effective."
            )
        return confirm


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


class ProviderGlobalSearchForm(forms.Form):
    search = forms.CharField(
        label="Recherche",
        help_text=mark_safe(
            """Recherche sur le nom d'une administration publique, d'une entreprise, un
            <a href="https://www.service-public.fr/professionnels-entreprises/vosdroits/F32135" tabindex="-1" target="_blank">numéro SIRET</a>,
            l'adresse, l\'activité ou le
            <a href="https://www.insee.fr/fr/information/2406147" tabindex="-1" target="_blank">code NAF</a>."""
        ),
        required=True,
        widget=forms.TextInput(
            attrs={"placeholder": "ex. Mairie", "autocomplete": "off"}
        ),
    )
    commune_search = forms.CharField(widget=forms.HiddenInput)
    code_insee = forms.CharField(
        label="Commune",
        required=True,
        help_text="Commencez à saisir le nom de la commune recherchée, puis sélectionnez la proposition correspondante.",
        widget=forms.Select(),
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        code_insee = initial.get("code_insee")
        if code_insee:
            commune = Commune.objects.filter(code_insee=code_insee).first()
            if commune:
                nom_departement = departements.DEPARTEMENTS[commune.departement]["nom"]
                commune_search = (
                    f"{commune.nom} ({commune.departement} - {nom_departement})"
                )
                initial["commune_search"] = commune_search
                initial["code_insee"] = code_insee
        super().__init__(*args, **kwargs)


class PublicPublicationForm(forms.ModelForm):
    class Meta:
        model = Accessibilite
        fields = (
            "user_type",
            "registre_url",
            "conformite",
        )
        help_texts = schema.get_help_texts()

    user_type = forms.ChoiceField(
        label="Mon profil",
        help_text="À quel titre contribuez vous les informations pour cet établissement ?",
        choices=[
            (
                Erp.USER_ROLE_PUBLIC,
                "Je fréquente cet établissement",
            ),
            (
                Erp.USER_ROLE_GESTIONNAIRE,
                "Je gère cet établissement",
            ),
            (
                Erp.USER_ROLE_ADMIN,
                "Je représente une administration publique",
            ),
        ],
        widget=forms.RadioSelect(attrs={"class": "inline"}),
        required=True,
    )
    registre_url = forms.URLField(
        label="Registre d'accessibilité",
        help_text=schema.get_help_text("registre_url"),
        widget=forms.TextInput(
            attrs={"type": "url", "placeholder": "http://", "autocomplete": "off"}
        ),
        required=False,
    )
    conformite = forms.ChoiceField(
        label="Conformité",
        help_text=schema.get_help_text("conformite"),
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "inline"}),
        required=False,
    )
    published = forms.BooleanField(
        label="Je souhaite mettre en ligne cette fiche d'établissement immédiatement",
        required=False,
    )
    certif = forms.BooleanField(
        label=f"Je certifie sur l'honneur l'exactitude de ces informations et consens à leur publication sur {settings.SITE_NAME}.",
        required=True,
    )

    def clean_certif(self):
        if not self.cleaned_data.get("certif", False):
            raise ValidationError(
                "Publication impossible sans ces garanties de votre part"
            )
        return True

    def clean_registre_url(self):
        url = self.cleaned_data.get("registre_url")
        if not url:
            return None
        try:
            req = requests.head(self.cleaned_data["registre_url"])
            if not req.ok:
                raise ValidationError(
                    f"Cette URL est en erreur HTTP {req.status_code}, veuillez vérifier votre saisie."
                )
        except RequestException:
            raise ValidationError(
                "Cette URL n'aboutit pas, veuillez vérifier votre saisie."
            )
        return url


class PublicClaimForm(forms.Form):
    ok = forms.BooleanField(
        required=True,
        label="Je m'engage sur l'honneur à fournir des informations factuelles sur cet établissement.",
    )
