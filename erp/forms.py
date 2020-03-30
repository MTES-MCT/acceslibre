from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError
from django.forms import fields, widgets

from . import geocoder
from .models import Activite, Accessibilite, Erp


def bool_radios():
    return forms.RadioSelect(attrs={"class": "inline"})


def get_widgets_for_accessibilite():
    # Note: commented fields are those not being custom boolean fields
    field_names = [
        "stationnement_presence",
        "stationnement_pmr",
        "stationnement_ext_presence",
        "stationnement_ext_pmr",
        "cheminement_ext_plain_pied",
        # "cheminement_ext_nombre_marches",
        "cheminement_ext_reperage_marches",
        "cheminement_ext_main_courante",
        "cheminement_ext_rampe",
        "cheminement_ext_ascenseur",
        "cheminement_ext_pente",
        "cheminement_ext_devers",
        "cheminement_ext_bande_guidage",
        "cheminement_ext_guidage_sonore",
        "cheminement_ext_retrecissement",
        "entree_reperage",
        "entree_vitree",
        "entree_vitree_vitrophanie",
        "entree_plain_pied",
        # "entree_marches",
        "entree_marches_reperage",
        "entree_marches_main_courante",
        "entree_marches_rampe",
        "entree_dispositif_appel",
        "entree_aide_humaine",
        "entree_ascenseur",
        # "entree_largeur_mini",
        "entree_pmr",
        # "entree_pmr_informations",
        "accueil_visibilite",
        "accueil_personnels",
        "accueil_equipements_malentendants",
        "accueil_cheminement_plain_pied",
        # "accueil_cheminement_nombre_marches",
        "accueil_cheminement_reperage_marches",
        "accueil_cheminement_main_courante",
        "accueil_cheminement_rampe",
        "accueil_cheminement_ascenseur",
        "accueil_retrecissement",
        # "accueil_prestations",
        "sanitaires_presence",
        # "sanitaires_adaptes",
        # "labels",
        # "labels_autre",
        # "commentaire",
    ]
    widgets = dict([(f, bool_radios()) for f in field_names])
    widgets.update(
        # if you've ever looked for a way to simply render a postgres ArrayField
        # using checkboxes, this is it.
        labels_familles_handicap=forms.CheckboxSelectMultiple(
            choices=Accessibilite.HANDICAP_CHOICES
        )
    )
    return widgets


class AdminAccessibiliteForm(forms.ModelForm):
    class Meta:
        model = Accessibilite
        exclude = ("pk",)
        widgets = get_widgets_for_accessibilite()


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


class AdminErpForm(forms.ModelForm):
    class Meta:
        model = Erp
        exclude = (
            "pk",
            "user",
            "search_vector",
        )

    def __init__(self, *args, geocode=None, **kwargs):
        self.geocode = geocode if geocode else geocoder.geocode
        return super().__init__(*args, **kwargs)

    def get_adresse(self):
        parts = [
            self.cleaned_data[f]
            for f in ["numero", "voie", "lieu_dit", "code_postal", "commune",]
            if f in self.cleaned_data and self.cleaned_data[f] is not None
        ]
        return " ".join(parts).strip()

    def clean(self):
        addr = self.get_adresse()
        if addr == "":
            return
        locdata = self.geocode(addr)
        if not locdata or locdata["geom"] is None:
            raise ValidationError({"voie": f"Adresse non localisable: {addr}."})
        else:
            # FIXME: would be nice to allow just setting custom geom
            self.cleaned_data["geom"] = locdata["geom"]
            self.cleaned_data["numero"] = locdata["numero"]
            self.cleaned_data["voie"] = locdata["voie"]
            self.cleaned_data["lieu_dit"] = locdata["lieu_dit"]
            self.cleaned_data["code_postal"] = locdata["code_postal"]
            self.cleaned_data["commune"] = locdata["commune"]
            self.cleaned_data["code_insee"] = locdata["code_insee"]


class ViewAccessibiliteForm(forms.ModelForm):
    class Meta:
        model = Accessibilite
        exclude = ("pk", "erp", "labels")

    fieldsets = {
        "Entrée": {
            "icon": "entrance",
            "tabid": "entree",
            "fields": [
                "entree_reperage",
                "entree_vitree",
                "entree_vitree_vitrophanie",
                "entree_plain_pied",
                "entree_marches",
                "entree_marches_reperage",
                "entree_marches_main_courante",
                "entree_marches_rampe",
                "entree_dispositif_appel",
                "entree_aide_humaine",
                "entree_ascenseur",
                "entree_largeur_mini",
                "entree_pmr",
                "entree_pmr_informations",
            ],
        },
        "Stationnement": {
            "icon": "car",
            "tabid": "stationnement",
            "fields": [
                "stationnement_presence",
                "stationnement_pmr",
                "stationnement_ext_presence",
                "stationnement_ext_pmr",
            ],
        },
        "Cheminement extérieur": {
            "icon": "path",
            "tabid": "cheminement_ext",
            "fields": [
                "cheminement_ext_plain_pied",
                "cheminement_ext_nombre_marches",
                "cheminement_ext_reperage_marches",
                "cheminement_ext_main_courante",
                "cheminement_ext_rampe",
                "cheminement_ext_ascenseur",
                "cheminement_ext_pente",
                "cheminement_ext_devers",
                "cheminement_ext_bande_guidage",
                "cheminement_ext_guidage_sonore",
                "cheminement_ext_retrecissement",
            ],
        },
        "Accueil": {
            "icon": "users",
            "tabid": "accueil",
            "fields": [
                "accueil_visibilite",
                "accueil_personnels",
                "accueil_equipements_malentendants",
                "accueil_cheminement_plain_pied",
                "accueil_cheminement_nombre_marches",
                "accueil_cheminement_reperage_marches",
                "accueil_cheminement_main_courante",
                "accueil_cheminement_rampe",
                "accueil_cheminement_ascenseur",
                "accueil_retrecissement",
                "accueil_prestations",
            ],
        },
        "Sanitaires": {
            "icon": "male-female",
            "tabid": "sanitaires",
            "fields": ["sanitaires_presence", "sanitaires_adaptes",],
        },
        "Commentaire": {
            "icon": "info-circled",
            "tabid": "commentaire",
            "fields": ["commentaire"],
        },
    }

    def get_accessibilite_data(self):
        data = {}
        for section, info in self.fieldsets.items():
            data[section] = {
                "icon": info["icon"],
                "tabid": info["tabid"],
                "fields": [],
            }
            for field_name in info["fields"]:
                field = self[field_name]
                # TODO: deconstruct field to make it serializable -> future API
                data[section]["fields"].append(field)
        return data
