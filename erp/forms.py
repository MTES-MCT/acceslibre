from django import forms
from django.core.exceptions import ValidationError

from .geocode import geocode
from .models import Accessibilite, Cheminement, Erp


def bool_radios():
    return forms.RadioSelect(attrs={"class": "inline"})


class AdminCheminementForm(forms.ModelForm):
    class Meta:
        model = Cheminement
        exclude = ("pk",)
        widgets = dict(
            [
                (f, bool_radios())
                for f in [
                    "pente",
                    "devers",
                    "reperage_vitres",
                    "bande_guidage",
                    "guidage_sonore",
                    "rampe",
                    "aide_humaine",
                    "escalier_reperage",
                    "escalier_main_courante",
                    "ascenseur",
                ]
            ]
        )


class AdminAccessibiliteForm(forms.ModelForm):
    class Meta:
        model = Accessibilite
        exclude = ("pk",)
        widgets = dict(
            [
                (f, bool_radios())
                for f in [
                    "entree_plain_pied",
                    "stationnement_presence",
                    "stationnement_pmr",
                    "stationnement_ext_presence",
                    "stationnement_ext_pmr",
                    "entree_plain_pied",
                    "entree_reperage",
                    "entree_interphone",
                    "entree_pmr",
                    "reperage_vitres",
                    "guidage_sonore",
                    "rampe",
                    "aide_humaine",
                    "escalier_reperage",
                    "escalier_main_courante",
                    "ascenseur",
                    "accueil_visibilite",
                    "accueil_personnels",
                    "accueil_equipements_malentendants",
                    "sanitaires_presence",
                ]
            ]
        )


class AdminErpForm(forms.ModelForm):
    class Meta:
        model = Erp
        exclude = ("pk",)

    def get_adresse(self):
        return " ".join(
            [
                self.cleaned_data[f]
                for f in [
                    "numero",
                    "voie",
                    "lieu_dit",
                    "code_postal",
                    "commune",
                ]
                if self.cleaned_data[f] is not None
            ]
        )

    def clean(self):
        addr = self.get_adresse()
        locdata = geocode(addr)
        if locdata["geom"] is None:
            raise ValidationError({"voie": f"Adresse non localisable: {addr}."})
        # FIXME: would be nice to allow just setting custom geom
        self.cleaned_data["geom"] = locdata["geom"]
        self.cleaned_data["numero"] = locdata["numero"]
        self.cleaned_data["voie"] = locdata["voie"]
        self.cleaned_data["lieu_dit"] = locdata["lieu_dit"]
        self.cleaned_data["code_postal"] = locdata["code_postal"]
        self.cleaned_data["commune"] = locdata["commune"]
        self.cleaned_data["code_insee"] = locdata["code_insee"]


class ViewCheminementForm(forms.ModelForm):
    class Meta:
        model = Cheminement
        exclude = ("pk", "accessibilite", "type", "nom")


class ViewAccessibiliteForm(forms.ModelForm):
    class Meta:
        model = Accessibilite
        exclude = ("pk", "erp", "labels")

    fieldsets = {
        "Entrée": {
            "icon": "entrance",
            "tabid": "entree",
            "fields": [
                "entree_plain_pied",
                "entree_reperage",
                "entree_pmr",
                "entree_pmr_informations",
                "entree_interphone",
                "reperage_vitres",
                "guidage_sonore",
                "largeur_mini",
                "rampe",
                "aide_humaine",
                "escalier_marches",
                "escalier_reperage",
                "escalier_main_courante",
                "ascenseur",
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
        "Accueil": {
            "icon": "users",
            "tabid": "accueil",
            "fields": [
                "accueil_visibilite",
                "accueil_personnels",
                "accueil_equipements_malentendants",
                "accueil_prestations",
            ],
        },
        "Sanitaires": {
            "icon": "male-female",
            "tabid": "sanitaires",
            "fields": ["sanitaires_presence", "sanitaires_adaptes",],
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
        cheminements = self.instance.cheminement_set.all()
        if len(cheminements) > 0:
            data["Cheminements"] = {
                "icon": "path",
                "tabid": "cheminements",
                "sections": {},
            }
            for cheminement in cheminements:
                section = (
                    cheminement.get_type_display() + " : " + cheminement.nom
                )
                form = ViewCheminementForm(instance=cheminement)
                data["Cheminements"]["sections"][section] = {
                    "icon": "path",
                    "tabid": cheminement.type,
                    "fields": [],
                }
                for field_name in form.fields:
                    # TODO: deconstruct field to make it serializable -> future API
                    field = form[field_name]
                    data["Cheminements"]["sections"][section]["fields"].append(
                        field
                    )
        return data
