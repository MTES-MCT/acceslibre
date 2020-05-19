from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError
from django.forms import fields, widgets

from . import geocoder
from .models import (
    Activite,
    Accessibilite,
    Commune,
    Erp,
    NULLABLE_OR_NA_BOOLEAN_CHOICES,
)

ACCESSIBILITE_HELP_TEXTS = {
    "transport_station_presence": "L'établissement est-il desservi par les transports en commun ?",
    "transport_information": "Préciser ici les informations supplémentaires sur ces transports (type de transport, ligne, nom de l'arrêt, etc) et éventuellement des informations jugées importantes sur le cheminement qui relie le point d'arrêt à l'établissement.",
    "stationnement_presence": "Existe-t-il une ou plusieurs places de stationnement dans l’établissement ou au sein de la parcelle de l’établissement ?",
    "stationnement_pmr": "Existe-t-il une ou plusieurs places de stationnement adaptées dans l’établissement ou au sein de la parcelle de l'établissement ?",
    "stationnement_ext_presence": "Existe-t-il une ou plusieurs places de stationnement en voirie ou en parking à proximité de l'établissement (200 m) ?",
    "stationnement_ext_pmr": "Existe-t-il une ou plusieurs places de stationnement adaptées en voirie ou en parking à proximité de l’établissement (200 m) ?",
    "cheminement_ext_presence": "L'établissement dispose-t-il d'un espace extérieur qui lui appartient ?",
    "cheminement_ext_terrain_accidente": "Le revêtement du cheminement extérieur (entre l’entrée de la parcelle et l’entrée de l’établissement) est-il meuble ou accidenté (pavés, gravillons, terre, herbe, ou toute surface non stabilisée) ?",
    "cheminement_ext_plain_pied": "Le cheminement est-il de plain-pied, c’est-à-dire sans marche ni ressaut supérieur à 2 cm ?  Attention plain-pied ne signifie pas plat mais sans rupture brutale de niveau.",
    "cheminement_ext_ascenseur": "Existe-t-il un ascenseur ou un élévateur ?",
    "cheminement_ext_nombre_marches": "Indiquer 0 s'il n'y a ni marche ni escalier",
    "cheminement_ext_reperage_marches": "L'escalier est-il sécurisé : nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées ?",
    "cheminement_ext_main_courante": "L'escalier est-il équipé d'une main courante ?",
    "cheminement_ext_rampe": "S'il existe une rampe, est-elle fixe ou amovible ?",
    "cheminement_ext_pente": "S'il existe une pente, quel est son degré de difficulté ?",
    "cheminement_ext_devers": "Un dévers est une inclinaison transversale du cheminement. S'il en existe un, quel est son degré de difficulté ?",
    "cheminement_ext_bande_guidage": "Présence d'une bande de guidage au sol facilitant le déplacement d'une personne aveugle ou malvoyante",
    "cheminement_ext_retrecissement": "Existe-t-il un ou plusieurs rétrécissements (inférieur à 80 cm) du chemin emprunté par le public pour atteindre l'entrée ?",
    "entree_reperage": "Y a-t-il des éléments facilitant le repérage de l'entrée de l’établissement (numéro de rue à proximité, enseigne, etc) ?",
    "entree_vitree": "La porte d'entrée est-elle vitrée ?",
    "entree_vitree_vitrophanie": "Si l'entrée est vitrée, y a-t-il des éléments contrastés permettant de visualiser les parties vitrées de l'entrée ? ",
    "entree_plain_pied": "L'entrée est-elle de plain-pied, c’est-à-dire sans marche ni ressaut supérieur à 2 cm ?",
    "entree_ascenseur": "Existe-t-il un ascenseur ou un élévateur ?",
    "entree_marches": "Indiquer 0 s'il n'y a ni marche ni escalier",
    "entree_marches_reperage": "L'escalier est-il sécurisé : nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées ?",
    "entree_marches_main_courante": "L'escalier est-il équipé d'une main courante ?",
    "entree_marches_rampe": "S'il existe une rampe, est-elle fixe ou amovible ?",
    "entree_balise_sonore": "L'entrée est-elle équipée d'une balise sonore facilitant son repérage par une personne aveugle ou malvoyante ?",
    "entree_dispositif_appel": "Existe-t-il un dispositif comme une sonnette pour permettre à quelqu'un ayant besoin de la rampe ou d'une aide humaine de signaler sa présence ?",
    "entree_aide_humaine": "Présence ou possibilité d'une aide humaine au déplacement",
    "entree_largeur_mini": "Si la largeur n'est pas précisément connue, indiquer une valeur minimum. Exemple : la largeur se situe entre 90 et 100 cm ; indiquer 90",
    "entree_pmr": "Existe-t-il une entrée secondaire spécifique dédiée aux personnes à mobilité réduite ?",
    "entree_pmr_informations": "Préciser ici les modalités d'accès de l'entrée spécifique PMR",
    "accueil_visibilite": "La zone d'accueil (guichet d’accueil, caisse, secrétariat, etc) est-elle visible depuis l'entrée ?",
    "accueil_personnels": "En cas de présence du personnel, est-il formé ou sensibilisé à l'accueil des personnes handicapées ?",
    "accueil_equipements_malentendants": "L'accueil est-il équipé de produits ou prestations dédiés aux personnes sourdes ou malentendantes (boucle à induction magnétique, langue des signes françaises, solution de traduction à distance, etc)",
    "accueil_cheminement_plain_pied": "Le cheminement est-il de plain-pied, c’est-à-dire sans marche ni ressaut supérieur à 2 cm ? Attention, plain-pied ne signifie pas plat mais sans rupture brutale de niveau.",
    "accueil_cheminement_nombre_marches": "Indiquer 0 s'il n'y a ni marche ni escalier",
    "accueil_cheminement_reperage_marches": "L'escalier est-il sécurisé : nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées ?",
    "accueil_cheminement_main_courante": "L'escalier est-il équipé d'une main courante ?",
    "accueil_cheminement_rampe": "S'il existe une rampe, est-elle fixe ou amovible ?",
    "accueil_cheminement_ascenseur": "Existe-t-il un ascenseur ou un élévateur ?",
    "sanitaires_presence": "Y a-t-il des sanitaires mis à disposition du public ?",
    "sanitaires_adaptes": "Combien y a-t-il de sanitaires adaptés ?",
    "labels": "Si l’établissement est entré dans une démarche volontaire de labellisation, quelle marque ou quel label a-t-il obtenu ?",
    "labels_familles_handicap": "Quelle(s) famille(s) de handicap sont couvertes par la marque ou le label ?",
    "labels_autre": "Si autre, préciser le nom du label",
    "commentaire": "Indiquer ici toute autre information qui semble pertinente pour décrire l'accessibilité du bâtiment",
}


def bool_radios():
    return forms.RadioSelect(attrs={"class": "inline"})


def get_widgets_for_accessibilite():
    # Note: commented fields are those not being custom boolean fields
    field_names = [
        "transport_station_presence",
        # "transport_information",
        "stationnement_presence",
        "stationnement_pmr",
        "stationnement_ext_presence",
        "stationnement_ext_pmr",
        "cheminement_ext_presence",
        "cheminement_ext_terrain_accidente",
        "cheminement_ext_plain_pied",
        "cheminement_ext_ascenseur",
        # "cheminement_ext_nombre_marches",
        "cheminement_ext_reperage_marches",
        "cheminement_ext_main_courante",
        "cheminement_ext_rampe",
        "cheminement_ext_pente",
        "cheminement_ext_devers",
        "cheminement_ext_bande_guidage",
        "cheminement_ext_retrecissement",
        "entree_reperage",
        "entree_vitree",
        "entree_vitree_vitrophanie",
        "entree_plain_pied",
        "entree_balise_sonore",
        "entree_dispositif_appel",
        # "entree_largeur_mini",
        "entree_pmr",
        # "entree_pmr_informations",
        # "entree_marches",
        "entree_marches_reperage",
        "entree_marches_main_courante",
        "entree_marches_rampe",
        "entree_aide_humaine",
        "entree_ascenseur",
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
        # "labels_familles_handicap",
        # "labels_autre",
        # "commentaire",
    ]
    return dict([(f, bool_radios()) for f in field_names])


class AdminAccessibiliteForm(forms.ModelForm):
    class Meta:
        model = Accessibilite
        exclude = ("pk",)
        widgets = get_widgets_for_accessibilite()
        help_texts = ACCESSIBILITE_HELP_TEXTS

    labels_familles_handicap = forms.MultipleChoiceField(
        required=False,
        choices=Accessibilite.HANDICAP_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="Famille(s) de handicap concernées(s)",
        help_text="Liste des familles de handicaps couverts par l'obtention de ce label",
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

    fieldsets = {
        "Transport en commun": {
            "icon": "bus",
            "tabid": "transport",
            "description": "Desserte par les transports en commun",
            "fields": [
                {"name": "transport_station_presence"},
                {"name": "transport_information"},
            ],
        },
        "Stationnement": {
            "icon": "car",
            "tabid": "stationnement",
            "description": "Emplacements de stationnement",
            "fields": [
                {"name": "stationnement_presence", "warn_if": False},
                {"name": "stationnement_pmr", "warn_if": False},
                {"name": "stationnement_ext_presence", "warn_if": False},
                {"name": "stationnement_ext_pmr", "warn_if": False},
            ],
        },
        "Espace et cheminement extérieur": {
            "icon": "exterieur-target",
            "tabid": "cheminement_ext",
            "description": "Abords extérieurs appartenant à l'établissement",
            "fields": [
                {"name": "cheminement_ext_presence"},
                {"name": "cheminement_ext_terrain_accidente", "warn_if": True},
                {"name": "cheminement_ext_plain_pied", "warn_if": False},
                {
                    "name": "cheminement_ext_nombre_marches",
                    "warn_if": lambda x, i: x and x > 0,
                },
                {"name": "cheminement_ext_reperage_marches", "warn_if": False},
                {"name": "cheminement_ext_main_courante", "warn_if": False},
                {
                    "name": "cheminement_ext_rampe",
                    "warn_if": Accessibilite.RAMPE_AUCUNE,
                },
                {"name": "cheminement_ext_ascenseur", "warn_if": False},
                {
                    "name": "cheminement_ext_pente",
                    "warn_if": lambda x, i: x
                    and x
                    in [Accessibilite.PENTE_LEGERE, Accessibilite.PENTE_IMPORTANTE],
                },
                {
                    "name": "cheminement_ext_devers",
                    "warn_if": lambda x, i: x
                    and x
                    in [Accessibilite.DEVERS_LEGER, Accessibilite.DEVERS_IMPORTANT],
                },
                {"name": "cheminement_ext_bande_guidage", "warn_if": False},
                {"name": "cheminement_ext_retrecissement", "warn_if": True},
            ],
        },
        "Entrée": {
            "icon": "entrance",
            "tabid": "entree",
            "description": "Entrée de l'établissement",
            "fields": [
                {"name": "entree_reperage", "warn_if": False},
                {"name": "entree_vitree", "warn_if": True},
                {"name": "entree_vitree_vitrophanie", "warn_if": False},
                {"name": "entree_plain_pied", "warn_if": False},
                {"name": "entree_marches", "warn_if": lambda x, i: x and x > 0},
                {"name": "entree_marches_reperage", "warn_if": False},
                {"name": "entree_marches_main_courante", "warn_if": False},
                {"name": "entree_marches_rampe", "warn_if": False},
                {"name": "entree_dispositif_appel", "warn_if": False},
                {"name": "entree_aide_humaine", "warn_if": False},
                {"name": "entree_ascenseur", "warn_if": False},
                {"name": "entree_largeur_mini", "warn_if": lambda x, i: x and x < 80},
                {"name": "entree_pmr", "warn_if": False},
                {"name": "entree_pmr_informations"},
            ],
        },
        "Accueil": {
            "icon": "users",
            "tabid": "accueil",
            "description": "Zone et prestations d'accueil",
            "fields": [
                {"name": "accueil_visibilite", "warn_if": False},
                {
                    "name": "accueil_personnels",
                    "warn_if": lambda x, i: x
                    and x
                    in [
                        Accessibilite.PERSONNELS_NON_FORMES,
                        Accessibilite.PERSONNELS_AUCUN,
                    ],
                },
                {
                    "name": "accueil_equipements_malentendants",
                    "warn_if": lambda x, i: i.id
                    and "Aucun"
                    in [eq.nom for eq in i.accueil_equipements_malentendants.all()],
                },
                {"name": "accueil_cheminement_plain_pied", "warn_if": False},
                {
                    "name": "accueil_cheminement_nombre_marches",
                    "warn_if": lambda x, i: x and x > 0,
                },
                {"name": "accueil_cheminement_reperage_marches", "warn_if": False},
                {"name": "accueil_cheminement_main_courante", "warn_if": False},
                {"name": "accueil_cheminement_rampe", "warn_if": False},
                {"name": "accueil_cheminement_ascenseur", "warn_if": False},
                {"name": "accueil_retrecissement", "warn_if": True},
                {"name": "accueil_prestations"},
            ],
        },
        "Sanitaires": {
            "icon": "male-female",
            "tabid": "sanitaires",
            "description": "Toilettes, WC",
            "fields": [
                {"name": "sanitaires_presence", "warn_if": False},
                {"name": "sanitaires_adaptes", "warn_if": lambda x, i: x and x < 1},
            ],
        },
        "Commentaire": {
            "icon": "info-circled",
            "tabid": "commentaire",
            "description": "Informations complémentaires",
            "fields": [{"name": "commentaire"}],
        },
    }

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
                field = self[field_data["name"]]
                field_value = field.value()
                if field_value == []:
                    field_value = None
                warning = None
                if "warn_if" in field_data:
                    if callable(field_data["warn_if"]):
                        warning = field_data["warn_if"](field_value, self.instance)
                    else:
                        warning = field_value == field_data["warn_if"]
                data[section]["fields"].append(
                    {
                        "template_name": field.field.widget.template_name,
                        "name": field.name,
                        "label": field.label,
                        "help_text": ACCESSIBILITE_HELP_TEXTS.get(
                            field.name, field.help_text
                        ),
                        "value": field_value,
                        "warning": warning,
                    }
                )
            # Discard empty sections to avoid rendering empty menu items
            empty_section = all(
                self[f["name"]].value() in [None, "", []] for f in section_fields
            )
            if empty_section:
                data.pop(section)
        return data
