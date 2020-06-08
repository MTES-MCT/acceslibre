from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError
from django.forms import widgets

from . import schema
from . import geocoder
from . import sirene
from .models import (
    Activite,
    Accessibilite,
    Commune,
    Erp,
)


def bool_radios():
    return forms.RadioSelect(attrs={"class": "inline"})


def get_widgets_for_accessibilite():
    field_names = schema.get_nullable_bool_fields()
    return dict([(f, bool_radios()) for f in field_names])


class AdminAccessibiliteForm(forms.ModelForm):
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


class AdminErpForm(forms.ModelForm):
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

    def __init__(self, *args, geocode=None, **kwargs):
        self.geocode = geocode if geocode else geocoder.geocode
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

    def clean(self):
        addr = self.get_adresse()
        if addr == "":
            return
        if self.cleaned_data["geom"] is None or self.adresse_changed():
            # User hasn't set a geom point yet, or the address has been manually
            # updated: we geocode the address
            locdata = self.geocode(addr)
            if not locdata or locdata["geom"] is None:
                raise ValidationError(
                    {
                        "voie": f"Adresse non localisable : {addr}. "
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


class PublicErpForm(forms.ModelForm):
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
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["activite"].required = True
        self.fields["activite"].help_text = "Domaine d'activité de l'établissement"


class PublicEtablissementSearchForm(forms.Form):
    nom = forms.CharField(label="Nom de l'établissement", required=False)
    code_postal = forms.CharField(label="Code postal de la commune", required=False)


class PublicSiretSearchForm(forms.Form):
    siret = forms.CharField(label="Numéro SIRET", required=False)

    def clean_siret(self):
        siret = sirene.validate_siret(self.cleaned_data["siret"])
        if not siret:
            raise ValidationError("Ce numéro SIRET est invalide")
        self.cleaned_data["siret"] = siret
        return self.cleaned_data["siret"]
