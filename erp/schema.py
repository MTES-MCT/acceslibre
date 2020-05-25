# This module is dedicated to describe, expose and handle accessibility fields data

UNKNOWN = "Inconnu"
UNKNOWN_OR_NA = "Inconnu ou sans objet"

NULLABLE_BOOLEAN_CHOICES = (
    (True, "Oui"),
    (False, "Non"),
    (None, UNKNOWN),
)

NULLABLE_OR_NA_BOOLEAN_CHOICES = (
    (True, "Oui"),
    (False, "Non"),
    (None, UNKNOWN_OR_NA),
)

DEVERS_AUCUN = "aucun"
DEVERS_LEGER = "léger"
DEVERS_IMPORTANT = "important"
DEVERS_CHOICES = [
    (DEVERS_AUCUN, "Aucun"),
    (DEVERS_LEGER, "Léger"),
    (DEVERS_IMPORTANT, "Important"),
    (None, UNKNOWN_OR_NA),
]

EQUIPEMENT_MALENTENDANT_AUCUN = "aucun"
EQUIPEMENT_MALENTENDANT_AUTRES = "autres"
EQUIPEMENT_MALENTENDANT_BIM = "bim"
EQUIPEMENT_MALENTENDANT_LSF = "lsf"
EQUIPEMENT_MALENTENDANT_SCD = "scd"
EQUIPEMENT_MALENTENDANT_CHOICES = [
    (EQUIPEMENT_MALENTENDANT_AUCUN, "Aucun"),
    (EQUIPEMENT_MALENTENDANT_AUTRES, "Autres"),
    (EQUIPEMENT_MALENTENDANT_BIM, "BIM"),
    (EQUIPEMENT_MALENTENDANT_LSF, "LSF"),
    (EQUIPEMENT_MALENTENDANT_SCD, "Service de communication à distance"),
]

HANDICAP_AUDITIF = "auditif"
HANDICAP_MENTAL = "mental"
HANDICAP_MOTEUR = "moteur"
HANDICAP_VISUEL = "visuel"
HANDICAP_CHOICES = [
    (HANDICAP_AUDITIF, "Auditif"),
    (HANDICAP_MENTAL, "Mental"),
    (HANDICAP_MOTEUR, "Moteur"),
    (HANDICAP_VISUEL, "Visuel"),
]

PENTE_AUCUNE = "aucune"
PENTE_LEGERE = "légère"
PENTE_IMPORTANTE = "importante"
PENTE_CHOICES = [
    (PENTE_AUCUNE, "Aucune"),
    (PENTE_LEGERE, "Légère"),
    (PENTE_IMPORTANTE, "Importante"),
    (None, UNKNOWN_OR_NA),
]

PERSONNELS_AUCUN = "aucun"
PERSONNELS_FORMES = "formés"
PERSONNELS_NON_FORMES = "non-formés"
PERSONNELS_CHOICES = [
    (PERSONNELS_AUCUN, "Aucun personnel"),
    (PERSONNELS_FORMES, "Personnels sensibilisés et formés"),
    (PERSONNELS_NON_FORMES, "Personnels non-formés"),
    (None, UNKNOWN),
]

RAMPE_AUCUNE = "aucune"
RAMPE_FIXE = "fixe"
RAMPE_AMOVIBLE = "amovible"
RAMPE_AIDE_HUMAINE = "aide humaine"
RAMPE_CHOICES = [
    (RAMPE_AUCUNE, "Aucune"),
    (RAMPE_FIXE, "Fixe"),
    (RAMPE_AMOVIBLE, "Amovible"),
    (None, UNKNOWN),
]

SECTION_TRANSPORT = "transport"
SECTION_STATIONNEMENT = "stationnement"
SECTION_CHEMINEMENT_EXT = "cheminement_ext"
SECTION_ENTREE = "entree"
SECTION_ACCUEIL = "accueil"
SECTION_SANITAIRES = "sanitaires"
SECTION_LABELS = "labels"
SECTION_COMMENTAIRE = "commentaire"
SECTIONS = {
    SECTION_TRANSPORT: {
        "icon": "bus",
        "label": "Transports en commun",
        "description": "Desserte par les transports en commun",
    },
    SECTION_STATIONNEMENT: {
        "icon": "car",
        "label": "Stationnement",
        "description": "Emplacements de stationnement",
    },
    SECTION_CHEMINEMENT_EXT: {
        "icon": "exterieur-target",
        "label": "Espace et cheminement extérieur",
        "description": "Abords extérieurs appartenant à l'établissement (hors voirie)",
    },
    SECTION_ENTREE: {
        "icon": "entrance",
        "label": "Entrée",
        "description": "Entrée de l'établissement",
    },
    SECTION_ACCUEIL: {
        "icon": "users",
        "label": "Accueil",
        "description": "Zone et prestations d'accueil",
    },
    SECTION_SANITAIRES: {
        "icon": "male-female",
        "label": "Sanitaires",
        "description": "Toilettes, WC",
    },
    SECTION_LABELS: {
        "icon": "tag",
        "label": "Marques ou labels d'accessibilité",
        "description": "Marques ou labels d'accessibilité",
    },
    SECTION_COMMENTAIRE: {
        "icon": "info-circled",
        "label": "Commentaire",
        "description": "Informations complémentaires",
    },
}

FIELDS = {
    # Transport
    "transport_station_presence": {
        "label": "Desserte par transports en commun",
        "help_text": "L'établissement est-il desservi par les transports en commun ?",
        "section": SECTION_TRANSPORT,
        "nullable_bool": True,
        "warn_if": None,
    },
    "transport_information": {
        "label": "Informations transports",
        "help_text": "Préciser ici les informations supplémentaires sur ces transports (type de transport, ligne, nom de l'arrêt, etc) et éventuellement des informations jugées importantes sur le cheminement qui relie le point d'arrêt à l'établissement.",
        "section": SECTION_TRANSPORT,
        "nullable_bool": False,
        "warn_if": None,
    },
    # Stationnement
    "stationnement_presence": {
        "label": "Stationnement dans l'ERP",
        "help_text": "Existe-t-il une ou plusieurs places de stationnement dans l’établissement ou au sein de la parcelle de l’établissement ?",
        "section": SECTION_STATIONNEMENT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "stationnement_pmr": {
        "label": "Stationnements PMR dans l'ERP",
        "help_text": "Existe-t-il une ou plusieurs places de stationnement adaptées dans l’établissement ou au sein de la parcelle de l'établissement ?",
        "section": SECTION_STATIONNEMENT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "stationnement_ext_presence": {
        "label": "Stationnement à proximité de l'ERP",
        "help_text": "Existe-t-il une ou plusieurs places de stationnement en voirie ou en parking à proximité de l'établissement (200 m) ?",
        "section": SECTION_STATIONNEMENT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "stationnement_ext_pmr": {
        "label": "Stationnements PMR à proximité de l'ERP",
        "help_text": "Existe-t-il une ou plusieurs places de stationnement adaptées en voirie ou en parking à proximité de l’établissement (200 m) ?",
        "section": SECTION_STATIONNEMENT,
        "nullable_bool": True,
        "warn_if": False,
    },
    # Cheminement extérieur
    "cheminement_ext_presence": {
        "label": "Espace extérieur",
        "help_text": "L'établissement dispose-t-il d'un espace extérieur qui lui appartient ?",
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": None,
    },
    "cheminement_ext_terrain_accidente": {
        "label": "Terrain meuble ou accidenté",
        "help_text": "Le revêtement du cheminement extérieur (entre l’entrée de la parcelle et l’entrée de l’établissement) est-il meuble ou accidenté (pavés, gravillons, terre, herbe, ou toute surface non stabilisée) ?",
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": True,
    },
    "cheminement_ext_plain_pied": {
        "label": "Cheminement de plain-pied",
        "help_text": "Le cheminement est-il de plain-pied, c’est-à-dire sans marche ni ressaut supérieur à 2 cm ?  Attention plain-pied ne signifie pas plat mais sans rupture brutale de niveau.",
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_ascenseur": {
        "label": "Ascenseur/élévateur",
        "help_text": "Existe-t-il un ascenseur ou un élévateur ?",
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_nombre_marches": {
        "label": "Nombre de marches",
        "help_text": "Indiquer 0 s'il n'y a ni marche ni escalier",
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x > 0,
    },
    "cheminement_ext_reperage_marches": {
        "label": "Repérage des marches ou de l’escalier",
        "help_text": "L'escalier est-il sécurisé : nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées ?",
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_main_courante": {
        "label": "Main courante",
        "help_text": "L'escalier est-il équipé d'une main courante ?",
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_rampe": {
        "label": "Rampe",
        "help_text": "S'il existe une rampe, est-elle fixe ou amovible ?",
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": RAMPE_AUCUNE,
    },
    "cheminement_ext_pente": {
        "label": "Pente",
        "help_text": "S'il existe une pente, quel est son degré de difficulté ?",
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None and x in [PENTE_LEGERE, PENTE_IMPORTANTE],
    },
    "cheminement_ext_devers": {
        "label": "Dévers",
        "help_text": "Un dévers est une inclinaison transversale du cheminement. S'il en existe un, quel est son degré de difficulté ?",
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None and x in [DEVERS_LEGER, DEVERS_IMPORTANT],
    },
    "cheminement_ext_bande_guidage": {
        "label": "Bande de guidage",
        "help_text": "Présence d'une bande de guidage au sol facilitant le déplacement d'une personne aveugle ou malvoyante",
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_retrecissement": {
        "label": "Rétrécissement du cheminement",
        "help_text": "Existe-t-il un ou plusieurs rétrécissements (inférieur à 80 cm) du chemin emprunté par le public pour atteindre l'entrée ?",
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": True,
    },
    # Entrée
    "entree_reperage": {
        "label": "Entrée facilement repérable",
        "help_text": "Y a-t-il des éléments facilitant le repérage de l'entrée de l’établissement (numéro de rue à proximité, enseigne, etc) ?",
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_vitree": {
        "label": "Entrée vitrée",
        "help_text": "La porte d'entrée est-elle vitrée ?",
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": True,
    },
    "entree_vitree_vitrophanie": {
        "label": "Vitrophanie",
        "help_text": "Si l'entrée est vitrée, y a-t-il des éléments contrastés permettant de visualiser les parties vitrées de l'entrée ? ",
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_plain_pied": {
        "label": "Entrée de plain-pied",
        "help_text": "L'entrée est-elle de plain-pied, c’est-à-dire sans marche ni ressaut supérieur à 2 cm ?",
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_ascenseur": {
        "label": "Ascenseur/élévateur",
        "help_text": "Existe-t-il un ascenseur ou un élévateur ?",
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_marches": {
        "label": "Marches ou escalier",
        "help_text": "Indiquer 0 s'il n'y a ni marche ni escalier",
        "section": SECTION_ENTREE,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x > 0,
    },
    "entree_marches_reperage": {
        "label": "Repérage des marches",
        "help_text": "L'escalier est-il sécurisé : nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées ?",
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_marches_main_courante": {
        "label": "Main courante",
        "help_text": "L'escalier est-il équipé d'une main courante ?",
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_marches_rampe": {
        "label": "Rampe",
        "help_text": "S'il existe une rampe, est-elle fixe ou amovible ?",
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_balise_sonore": {
        "label": "Balise sonore",
        "help_text": "L'entrée est-elle équipée d'une balise sonore facilitant son repérage par une personne aveugle ou malvoyante ?",
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_dispositif_appel": {
        "label": "Dispositif d'appel",
        "help_text": "Existe-t-il un dispositif comme une sonnette pour permettre à quelqu'un ayant besoin de la rampe ou d'une aide humaine de signaler sa présence ?",
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_aide_humaine": {
        "label": "Aide humaine",
        "help_text": "Présence ou possibilité d'une aide humaine au déplacement",
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_largeur_mini": {
        "label": "Largeur minimale",
        "help_text": "Si la largeur n'est pas précisément connue, indiquer une valeur minimum. Exemple : la largeur se situe entre 90 et 100 cm ; indiquer 90",
        "section": SECTION_ENTREE,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x < 80,
    },
    "entree_pmr": {
        "label": "Entrée spécifique PMR",
        "help_text": "Existe-t-il une entrée secondaire spécifique dédiée aux personnes à mobilité réduite ?",
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_pmr_informations": {
        "label": "Infos entrée spécifique PMR",
        "help_text": "Préciser ici les modalités d'accès de l'entrée spécifique PMR",
        "section": SECTION_ENTREE,
        "nullable_bool": False,
        "warn_if": None,
    },
    # Accueil
    "accueil_visibilite": {
        "label": "Visibilité de la zone d'accueil",
        "help_text": "La zone d'accueil (guichet d’accueil, caisse, secrétariat, etc) est-elle visible depuis l'entrée ?",
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_personnels": {
        "label": "Personnel d'accueil",
        "help_text": "En cas de présence du personnel, est-il formé ou sensibilisé à l'accueil des personnes handicapées ?",
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None
        and x in [PERSONNELS_NON_FORMES, PERSONNELS_AUCUN,],
    },
    "accueil_equipements_malentendants": {
        "label": "Équipements sourds/malentendants",
        "help_text": "L'accueil est-il équipé de produits ou prestations dédiés aux personnes sourdes ou malentendantes (boucle à induction magnétique, langue des signes françaises, solution de traduction à distance, etc)",
        "section": SECTION_ACCUEIL,
        "nullable_bool": False,
        "warn_if": lambda x, i: x and "aucun" in x,
    },
    "accueil_cheminement_plain_pied": {
        "label": "Cheminement de plain pied",
        "help_text": "Le cheminement est-il de plain-pied, c’est-à-dire sans marche ni ressaut supérieur à 2 cm ? Attention, plain-pied ne signifie pas plat mais sans rupture brutale de niveau.",
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_ascenseur": {
        "label": "Ascenseur/élévateur",
        "help_text": "Existe-t-il un ascenseur ou un élévateur ?",
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_nombre_marches": {
        "label": "Nombre de marches",
        "help_text": "Indiquer 0 s'il n'y a ni marche ni escalier",
        "section": SECTION_ACCUEIL,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x > 0,
    },
    "accueil_cheminement_reperage_marches": {
        "label": "Repérage des marches ou de l’escalier",
        "help_text": "L'escalier est-il sécurisé : nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées ?",
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_main_courante": {
        "label": "Main courante",
        "help_text": "L'escalier est-il équipé d'une main courante ?",
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_rampe": {
        "label": "Rampe",
        "help_text": "S'il existe une rampe, est-elle fixe ou amovible ?",
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_retrecissement": {
        "label": "Rétrécissement du cheminement",
        "help_text": "Existe-t-il un ou plusieurs rétrécissements (inférieur à 80 cm) du chemin emprunté par le public pour atteindre la zone d’accueil ?",
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": True,
    },
    "accueil_prestations": {
        "label": "Prestations d'accueil adapté supplémentaires",
        "help_text": "Prestations spécifiques supplémentaires proposées par l'établissement",
        "section": SECTION_ACCUEIL,
        "nullable_bool": False,
        "warn_if": None,
    },
    # Sanitaires
    "sanitaires_presence": {
        "label": "Sanitaires",
        "help_text": "Y a-t-il des sanitaires mis à disposition du public ?",
        "section": SECTION_SANITAIRES,
        "nullable_bool": True,
        "warn_if": False,
    },
    "sanitaires_adaptes": {
        "label": "Nombre de sanitaires adaptés",
        "help_text": "Combien y a-t-il de sanitaires adaptés ?",
        "section": SECTION_SANITAIRES,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x < 1,
    },
    # Labels
    "labels": {
        "label": "Marques ou labels",
        "help_text": "Si l’établissement est entré dans une démarche volontaire de labellisation, quelle marque ou quel label a-t-il obtenu ?",
        "section": SECTION_LABELS,
        "nullable_bool": False,
        "warn_if": None,
    },
    "labels_familles_handicap": {
        "label": "Famille(s) de handicap concernées(s)",
        "help_text": "Quelle(s) famille(s) de handicap sont couvertes par la marque ou le label ?",
        "section": SECTION_LABELS,
        "nullable_bool": False,
        "warn_if": None,
    },
    "labels_autre": {
        "label": "Autre label",
        "help_text": "Si autre, préciser le nom du label",
        "section": SECTION_LABELS,
        "nullable_bool": False,
        "warn_if": None,
    },
    # Commentaire
    "commentaire": {
        "label": "Commentaire libre",
        "help_text": "Indiquer ici toute autre information qui semble pertinente pour décrire l'accessibilité du bâtiment",
        "section": SECTION_COMMENTAIRE,
        "nullable_bool": False,
        "warn_if": None,
    },
}


def get_api_fieldsets():
    # {"id_section": {
    #   "label": "Nom de la section",
    #   "fields": ["id_champ1", "id_champ2"],
    # },
    fieldsets = {}
    for section_id, section in SECTIONS.items():
        fieldsets[section_id] = {
            "label": section["label"],
            "fields": get_section_fields(section_id),
        }
    return fieldsets


def get_admin_fieldsets():
    # [('Nom de la section',
    #   {'description': None,
    #    'fields': ['id_champ1', 'id_champ2']}),
    #   ...
    # ]
    fieldsets = {}
    for section_id, section in SECTIONS.items():
        fieldsets[section["label"]] = {
            "description": section.get("description"),
            "fields": get_section_fields(section_id),
        }
    return list(fieldsets.items())


def get_form_fieldsets(exclude_sections=None):
    # {"Nom de la section": {
    #   "icon": "icon_name",
    #   "tabid": "section_id",
    #   "description": "Description de la section",
    #   "fields": [
    #     {"id": "id_champ1", "warn_if": Bool,},
    #     {"id": "id_champ2", "warn_if": Bool,},
    #     ...
    #   ]
    # }}
    fieldsets = {}
    for section_id, section in SECTIONS.items():
        if exclude_sections and section_id in exclude_sections:
            continue
        fieldsets[section["label"]] = {
            "icon": section.get("icon"),
            "tabid": section_id,
            "description": section.get("description"),
            "fields": [
                dict(id=f, warn_if=FIELDS.get(f).get("warn_if"))
                for f in get_section_fields(section_id)
            ],
        }
    return fieldsets


def get_labels():
    return dict((k, v.get("label")) for (k, v) in FIELDS.items())


def get_label(field, default=""):
    try:
        return FIELDS[field].get("label", default)
    except KeyError:
        return default


def get_help_texts():
    return dict((k, v.get("help_text")) for (k, v) in FIELDS.items())


def get_help_text(field, default=""):
    try:
        return FIELDS[field].get("help_text", default)
    except KeyError:
        return default


def get_section_fields(section_id):
    return [k for (k, v) in FIELDS.items() if v["section"] == section_id]


def get_nullable_bool_fields():
    return [k for (k, v) in FIELDS.items() if v["nullable_bool"] == True]
