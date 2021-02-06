from django.utils.safestring import mark_safe

# This module describes and handles accessibility fields data

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

# Specific case where we want to map nullable bool choices
# to 0 and 1 integers (see sanitaires_adaptes field)
NULLABLE_BOOL_NUM_CHOICES = (
    (1, "Oui"),
    (0, "Non"),
    (None, UNKNOWN),
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

EQUIPEMENT_MALENTENDANT_AUTRES = "autres"
EQUIPEMENT_MALENTENDANT_BIM = "bim"
EQUIPEMENT_MALENTENDANT_LSF = "lsf"
EQUIPEMENT_MALENTENDANT_SCD = "scd"
EQUIPEMENT_MALENTENDANT_LPC = "lpc"
EQUIPEMENT_MALENTENDANT_CHOICES = [
    (EQUIPEMENT_MALENTENDANT_BIM, "Boucle à induction magnétique"),
    (EQUIPEMENT_MALENTENDANT_LSF, "Langue des signes française"),
    (EQUIPEMENT_MALENTENDANT_LPC, "Langue Française Parlée Complétée (LFPC)"),
    (EQUIPEMENT_MALENTENDANT_SCD, "Service de communication à distance"),
    (EQUIPEMENT_MALENTENDANT_AUTRES, "Autres"),
]

EQUIPEMENT_MALENTENDANT_DESCRIPTIONS = {
    EQUIPEMENT_MALENTENDANT_AUTRES: "Autres équipements non précisés",
    EQUIPEMENT_MALENTENDANT_BIM: "La boucle à induction magnétique (BIM) permet d'entendre une source sonore en s'affranchissant de la distance (salles de spectacles), du bruit ambiant (lieux publics), des phénomènes d'échos ou de réverbérations sonores (églises, salles aux murs nus), des déformations apportées par les écouteurs (téléphones, MP3) ou les haut-parleurs (télévision, radio, cinéma).",
    EQUIPEMENT_MALENTENDANT_LSF: "La langue des signes française (LSF) est la langue des signes utilisée par une partie des sourds de France et par une partie des sourds de Suisse.",
    EQUIPEMENT_MALENTENDANT_LPC: "Langue Française Parlée Complétée (LFPC)",
    EQUIPEMENT_MALENTENDANT_SCD: "Service de communication, à distance et en temps réel, entre entendants et malentendants ou sourds, par transcription TIP (Transcription Instantanée de la Parole) ou LSF (Langue des Signes Français).",
}

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

LABEL_AUTRE = "autre"
LABEL_DPT = "dpt"
LABEL_MOBALIB = "mobalib"
LABEL_TH = "th"
LABEL_CHOICES = [
    (LABEL_AUTRE, "Autre"),
    (LABEL_DPT, "Destination pour Tous"),
    (LABEL_MOBALIB, "Mobalib"),
    (LABEL_TH, "Tourisme & Handicap"),
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
    (PERSONNELS_FORMES, "Personnels sensibilisés ou formés"),
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

REGISTRE_INFO_URL = "https://handicap.gouv.fr/actualites/article/registre-d-accessibilite-obligatoire-un-guide-pour-les-erp"

PARTENAIRES = {
    "DGE": {
        "avatar": "dge_avatar.png",
        "logo": "img/partenaires/dge.png",
        "name": "DGE",
        "short_description": "Direction Générale des Entreprises",
        "template": "editorial/partenaires/dge.html",
        "url": "https://www.entreprises.gouv.fr/fr",
    },
    "JACCEDE": {
        "avatar": "jaccede_avatar.png",
        "logo": "img/partenaires/jaccede.png",
        "name": "Jaccede",
        "short_description": "Trouvez les lieux qui vous sont accessibles",
        "template": "editorial/partenaires/jaccede.html",
        "url": "https://jaccede.com/",
    },
    "LUCIE": {
        "avatar": "lucie_avatar.png",
        "logo": "img/partenaires/lucie.png",
        "name": "RSE Lucie",
        "short_description": "La RSE Positive",
        "template": "editorial/partenaires/lucie.html",
        "url": "https://agence-lucie.com/",
    },
    "MOBALIB": {
        "avatar": "mobalib_avatar.jpg",
        "logo": "img/partenaires/mobalib.png",
        "name": "Mobalib",
        "short_description": "Mobalib, l'expert du handicap",
        "template": "editorial/partenaires/mobalib.html",
        "url": "https://www.mobalib.com/",
    },
    "WEGOTO": {
        "avatar": "wegoto_avatar.png",
        "logo": "img/partenaires/wegoto.png",
        "name": "Wegoto",
        "short_description": "Expert en données d’accessibilité",
        "template": "editorial/partenaires/wegoto.html",
        "url": "https://www.wegoto.eu/",
    },
}

SECTION_TRANSPORT = "transport"
SECTION_STATIONNEMENT = "stationnement"
SECTION_CHEMINEMENT_EXT = "cheminement_ext"
SECTION_ENTREE = "entree"
SECTION_ACCUEIL = "accueil"
SECTION_SANITAIRES = "sanitaires"
SECTION_LABELS = "labels"
SECTION_REGISTRE = "registre"
SECTION_CONFORMITE = "conformite"
SECTION_COMMENTAIRE = "commentaire"
SECTIONS = {
    SECTION_TRANSPORT: {
        "icon": "bus",
        "label": "Transports en commun",
        "description": "Arrêt de transport en commun à proximité",
        "edit_route": "contrib_transport",
    },
    SECTION_STATIONNEMENT: {
        "icon": "car",
        "label": "Stationnement",
        "description": "Emplacements de stationnement",
        "edit_route": "contrib_stationnement",
    },
    SECTION_CHEMINEMENT_EXT: {
        "icon": "exterieur-target",
        "label": "Cheminement extérieur",
        "description": "Cheminement extérieur depuis la voirie jusqu'à l'entrée",
        "edit_route": "contrib_exterieur",
    },
    SECTION_ENTREE: {
        "icon": "entrance",
        "label": "Entrée",
        "description": "Entrée de l'établissement",
        "edit_route": "contrib_entree",
    },
    SECTION_ACCUEIL: {
        "icon": "users",
        "label": "Accueil",
        "description": "Zone et prestations d'accueil",
        "edit_route": "contrib_accueil",
    },
    SECTION_SANITAIRES: {
        "icon": "male-female",
        "label": "Sanitaires",
        "description": "Toilettes, WC",
        "edit_route": "contrib_sanitaires",
    },
    SECTION_LABELS: {
        "icon": "trophy",
        "label": "Marques ou labels",
        "description": "Marques ou labels d'accessibilité",
        "edit_route": "contrib_labellisation",
    },
    SECTION_REGISTRE: {
        "icon": "registre",
        "label": "Registre",
        "description": "Registre d'accessibilité de l'établissement",
        "edit_route": None,
    },
    SECTION_CONFORMITE: {
        "icon": "conformite",
        "label": "Conformité",
        "description": "Conformité",
        "edit_route": None,
    },
    SECTION_COMMENTAIRE: {
        "icon": "info-circled",
        "label": "Commentaire",
        "description": "Informations complémentaires",
        "edit_route": "contrib_commentaire",
    },
}

FIELDS = {
    # Transport
    "transport_station_presence": {
        "is_a11y": True,
        "label": "Proximité d'un arrêt de transport en commun",
        "help_text": mark_safe(
            "Existe-t-il un arrêt de transport en commun à proximité (moins de 200 mètres)&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Arrêt de transport en commun à proximité (moins de 200 mètres)"
        ),
        "section": SECTION_TRANSPORT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "transport_information": {
        "is_a11y": True,
        "label": "Informations complémentaires",
        "help_text": mark_safe(
            "Préciser ici les informations supplémentaires sur ces transports (type de transport, ligne, nom de l'arrêt, etc) et éventuellement des informations jugées importantes sur le cheminement qui relie le point d'arrêt à l'établissement."
        ),
        "help_text_ui": None,
        "section": SECTION_TRANSPORT,
        "nullable_bool": False,
        "warn_if": None,
    },
    # Stationnement
    "stationnement_presence": {
        "is_a11y": True,
        "label": "Stationnement dans l'ERP",
        "help_text": mark_safe(
            "Existe-t-il une ou plusieurs places de stationnement dans l’établissement ou au sein de la parcelle de l’établissement&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Présence de stationnement au sein de la parcelle de l'établissement"
        ),
        "section": SECTION_STATIONNEMENT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "stationnement_pmr": {
        "is_a11y": True,
        "label": "Stationnements adaptés dans l'ERP",
        "help_text": mark_safe(
            "Existe-t-il une ou plusieurs places de stationnement adaptées dans l’établissement ou au sein de la parcelle de l'établissement&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Présence de stationnement adapté au sein de la parcelle de l'établissement"
        ),
        "section": SECTION_STATIONNEMENT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "stationnement_ext_presence": {
        "is_a11y": True,
        "label": "Stationnement à proximité de l'ERP",
        "help_text": mark_safe(
            "Existe-t-il une ou plusieurs places de stationnement en voirie ou en parking à proximité de l'établissement (200 m)&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Présence de stationnement à proximité de l'établissement (moins de 200 mètres)"
        ),
        "section": SECTION_STATIONNEMENT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "stationnement_ext_pmr": {
        "is_a11y": True,
        "label": "Stationnements PMR à proximité de l'ERP",
        "help_text": mark_safe(
            "Existe-t-il une ou plusieurs places de stationnement adaptées en voirie ou en parking à proximité de l’établissement (200 m)&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Présence de stationnement adapté à proximité de l'établissement (moins de 200 mètres)"
        ),
        "section": SECTION_STATIONNEMENT,
        "nullable_bool": True,
        "warn_if": False,
    },
    # Cheminement extérieur
    "cheminement_ext_presence": {
        "is_a11y": True,
        "label": "Cheminement extérieur",
        "help_text": mark_safe(
            "L'accès à l'entrée depuis la voirie se fait-il par un cheminement extérieur&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "L'accès à l'entrée depuis la voirie se fait par un cheminement extérieur"
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": None,
    },
    "cheminement_ext_terrain_accidente": {
        "is_a11y": True,
        "label": "Revêtement extérieur",
        "help_text": mark_safe(
            "Le revêtement du cheminement extérieur (entre l’entrée de la parcelle et l’entrée de l’établissement) est-il meuble ou accidenté (pavés, gravillons, terre, herbe, ou toute surface non stabilisée)&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Cet revêtement est accidenté (pavés, gravillons, terre, herbe, sable, ou toute surface non stabilisée)"
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": True,
    },
    "cheminement_ext_plain_pied": {
        "is_a11y": True,
        "label": "Cheminement extérieur de plain-pied",
        "help_text": mark_safe(
            "Le cheminement est-il de plain-pied, c’est-à-dire sans marche ni ressaut supérieur à 2 cm&nbsp;? Attention plain-pied ne signifie pas plat mais sans rupture brutale de niveau."
        ),
        "help_text_ui": mark_safe(
            "L'accès à cet espace se fait de plain-pied (sans rupture de niveau)"
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_ascenseur": {
        "is_a11y": True,
        "label": "Ascenseur/élévateur",
        "help_text": mark_safe("Existe-t-il un ascenseur ou un élévateur&nbsp;?"),
        "help_text_ui": None,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_nombre_marches": {
        "is_a11y": True,
        "label": "Nombre de marches",
        "help_text": mark_safe("Indiquer 0 s'il n'y a ni marche ni escalier"),
        "help_text_ui": None,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x > 0,
    },
    "cheminement_ext_reperage_marches": {
        "is_a11y": True,
        "label": "Marches ou escalier sécurisé(es)",
        "help_text": mark_safe(
            "L'escalier est-il sécurisé&nbsp;: nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier et/ou première et dernière contremarches contrastées"
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_main_courante": {
        "is_a11y": True,
        "label": "Main courante",
        "help_text": mark_safe("L'escalier est-il équipé d'une main courante&nbsp;?"),
        "help_text_ui": None,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_rampe": {
        "is_a11y": True,
        "label": "Rampe",
        "help_text": mark_safe(
            "S'il existe une rampe, est-elle fixe ou amovible&nbsp;?"
        ),
        "help_text_ui": mark_safe("Présence et type de rampe"),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": RAMPE_AUCUNE,
    },
    "cheminement_ext_pente": {
        "is_a11y": True,
        "label": "Pente",
        "help_text": mark_safe(
            "S'il existe une pente, quel est son degré de difficulté&nbsp;?"
        ),
        "help_text_ui": None,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None and x in [PENTE_LEGERE, PENTE_IMPORTANTE],
    },
    "cheminement_ext_devers": {
        "is_a11y": True,
        "label": "Dévers",
        "help_text": mark_safe(
            "Un dévers est une inclinaison transversale du cheminement. S'il en existe un, quel est son degré de difficulté&nbsp;?"
        ),
        "help_text_ui": None,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None and x in [DEVERS_LEGER, DEVERS_IMPORTANT],
    },
    "cheminement_ext_bande_guidage": {
        "is_a11y": True,
        "label": "Bande de guidage",
        "help_text": mark_safe(
            "Présence d'une bande de guidage au sol facilitant le déplacement d'une personne aveugle ou malvoyante"
        ),
        "help_text_ui": mark_safe(
            "Présence d'une bande de guidage au sol facilitant le déplacement d'une personne aveugle ou malvoyante"
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_retrecissement": {
        "is_a11y": True,
        "label": "Rétrécissement du cheminement",
        "help_text": mark_safe(
            "Existe-t-il un ou plusieurs rétrécissements (inférieur à 80 cm) du chemin emprunté par le public pour atteindre l'entrée&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Un ou plusieurs rétrecissements (inférieurs à 80 cm) du chemin pour atteindre l'entrée"
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": True,
    },
    # Entrée
    "entree_reperage": {
        "is_a11y": True,
        "label": "Entrée facilement repérable",
        "help_text": mark_safe(
            "Y a-t-il des éléments facilitant le repérage de l'entrée de l’établissement (numéro de rue à proximité, enseigne, végétaux, éléments architecturaux contrastés, etc)&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Présence d'éléments facilitant le repérage de l'entrée de l’établissement (numéro de rue à proximité, enseigne, végétaux, éléments architecturaux contrastés, etc)"
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_vitree": {
        "is_a11y": True,
        "label": "Entrée vitrée",
        "help_text": mark_safe("La porte d'entrée est-elle vitrée&nbsp;?"),
        "help_text_ui": None,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": True,
    },
    "entree_vitree_vitrophanie": {
        "is_a11y": True,
        "label": "Repérage de la vitre",
        "help_text": mark_safe(
            "Y a-t-il des éléments contrastés (autocollants ou autres) permettant de repérer la porte vitrée&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Présence d'éléments contrastés permettant de visualiser les parties vitrées de l'entrée"
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_plain_pied": {
        "is_a11y": True,
        "label": "Entrée de plain-pied",
        "help_text": mark_safe(
            "L'entrée est-elle de plain-pied, c’est-à-dire sans marche ni ressaut supérieur à 2 cm&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "L'entrée se fait de plain-pied (sans rupture de niveau)"
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_ascenseur": {
        "is_a11y": True,
        "label": "Ascenseur/élévateur",
        "help_text": mark_safe("Existe-t-il un ascenseur ou un élévateur&nbsp;?"),
        "help_text_ui": None,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_marches": {
        "is_a11y": True,
        "label": "Nombre de marches",
        "help_text": mark_safe("Indiquer 0 s'il n'y a ni marche ni escalier"),
        "help_text_ui": None,
        "section": SECTION_ENTREE,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x > 0,
    },
    "entree_marches_reperage": {
        "is_a11y": True,
        "label": "Repérage des marches",
        "help_text": mark_safe(
            "L'escalier est-il sécurisé&nbsp;: nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier et/ou première et dernière contremarches contrastées"
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_marches_main_courante": {
        "is_a11y": True,
        "label": "Main courante",
        "help_text": mark_safe("L'escalier est-il équipé d'une main courante&nbsp;?"),
        "help_text_ui": None,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_marches_rampe": {
        "is_a11y": True,
        "label": "Rampe",
        "help_text": mark_safe(
            "S'il existe une rampe, est-elle fixe ou amovible&nbsp;?"
        ),
        "help_text_ui": None,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is False or x == RAMPE_AUCUNE,
    },
    "entree_dispositif_appel": {
        "is_a11y": True,
        "label": "Dispositif d'appel à l'entrée",
        "help_text": mark_safe(
            "Existe-t-il un dispositif comme une sonnette pour permettre à quelqu'un ayant besoin de la rampe ou d'une aide humaine de signaler sa présence&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Présence d'un dispositif comme une sonnette pour signaler sa présence"
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_balise_sonore": {
        "is_a11y": True,
        "label": "Balise sonore à l'entrée",
        "help_text": mark_safe(
            "L'entrée est-elle équipée d'une balise sonore facilitant son repérage par une personne aveugle ou malvoyante&nbsp;?"
        ),
        "help_text_ui": None,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_aide_humaine": {
        "is_a11y": True,
        "label": "Aide humaine",
        "help_text": mark_safe(
            "Présence ou possibilité d'une aide humaine au déplacement"
        ),
        "help_text_ui": None,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_largeur_mini": {
        "is_a11y": True,
        "label": "Largeur de la porte",
        "help_text": mark_safe(
            "Si la largeur n'est pas précisément connue, indiquer une valeur minimum. Exemple&nbsp;: la largeur se situe entre 90 et 100 cm&nbsp;; indiquer 90."
        ),
        "help_text_ui": mark_safe("Largeur minimale de la porte d'entrée"),
        "section": SECTION_ENTREE,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x < 80,
    },
    "entree_pmr": {
        "is_a11y": True,
        "label": "Entrée spécifique PMR",
        "help_text": mark_safe(
            "Existe-t-il une entrée secondaire spécifique dédiée aux personnes à mobilité réduite&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Présence d'une entrée secondaire spécifique dédiée aux personnes à mobilité réduite"
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_pmr_informations": {
        "is_a11y": True,
        "label": "Informations complémentaires concernant l'entrée PMR",
        "help_text": mark_safe(
            "Préciser ici les modalités d'accès de l'entrée spécifique PMR"
        ),
        "help_text_ui": None,
        "section": SECTION_ENTREE,
        "nullable_bool": False,
        "warn_if": None,
    },
    # Accueil
    "accueil_visibilite": {
        "is_a11y": True,
        "label": "Visibilité de la zone d'accueil",
        "help_text": mark_safe(
            "La zone d'accueil (guichet d’accueil, caisse, secrétariat, etc) est-elle visible depuis l'entrée&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "La zone d'accueil (guichet d’accueil, caisse, secrétariat, etc) est visible depuis l'entrée"
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_personnels": {
        "is_a11y": True,
        "label": "Personnel d'accueil",
        "help_text": mark_safe(
            "En cas de présence du personnel, est-il formé ou sensibilisé à l'accueil des personnes handicapées&nbsp;?"
        ),
        "help_text_ui": None,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None
        and x
        in [
            PERSONNELS_NON_FORMES,
            PERSONNELS_AUCUN,
        ],
    },
    "accueil_equipements_malentendants_presence": {
        "is_a11y": True,
        "label": "Présence d'équipements d'aide à l'audition et à la communication",
        "help_text": mark_safe(
            "L'accueil est-il équipé de produits ou prestations dédiés aux personnes sourdes ou malentendantes&nbsp?"
        ),
        "help_text_ui": mark_safe(
            "Présence de produits ou prestations dédiés aux personnes sourdes ou malentendantes"
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_equipements_malentendants": {
        "is_a11y": True,
        "label": "Liste des équipements d'aide à l'audition et à la communication",
        "help_text": mark_safe(
            "Sélectionnez les équipements ou prestations disponibles à l'accueil de l'établissement&nbsp;:"
        ),
        "help_text_ui": mark_safe("Équipements ou prestations disponibles"),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None and len(x) == 0,
    },
    "accueil_cheminement_plain_pied": {
        "is_a11y": True,
        "label": "Cheminement de plain-pied entre l'entrée et l'accueil",
        "help_text": mark_safe(
            "Le cheminement est-il de plain-pied, c’est-à-dire sans marche ni ressaut supérieur à 2 cm&nbsp;? Attention, plain-pied ne signifie pas plat mais sans rupture brutale de niveau."
        ),
        "help_text_ui": mark_safe(
            "L'accès à cet espace se fait de plain-pied (sans rupture de niveau)"
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_ascenseur": {
        "is_a11y": True,
        "label": "Ascenseur/élévateur",
        "help_text": mark_safe("Existe-t-il un ascenseur ou un élévateur&nbsp;?"),
        "help_text_ui": None,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_nombre_marches": {
        "is_a11y": True,
        "label": "Nombre de marches",
        "help_text": mark_safe("Indiquer 0 s'il n'y a ni marche ni escalier"),
        "help_text_ui": None,
        "section": SECTION_ACCUEIL,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x > 0,
    },
    "accueil_cheminement_reperage_marches": {
        "is_a11y": True,
        "label": "Repérage des marches ou de l’escalier",
        "help_text": mark_safe(
            "L'escalier est-il sécurisé&nbsp;: nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier et/ou première et dernière contremarches contrastées"
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_main_courante": {
        "is_a11y": True,
        "label": "Main courante",
        "help_text": mark_safe("L'escalier est-il équipé d'une main courante&nbsp;?"),
        "help_text_ui": None,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_rampe": {
        "is_a11y": True,
        "label": "Rampe",
        "help_text": mark_safe(
            "S'il existe une rampe, est-elle fixe ou amovible&nbsp;?"
        ),
        "help_text_ui": mark_safe("Présence et type de rampe"),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_retrecissement": {
        "is_a11y": True,
        "label": "Rétrécissement du cheminement",
        "help_text": mark_safe(
            "Existe-t-il un ou plusieurs rétrécissements (inférieur à 80 cm) du chemin emprunté par le public pour atteindre la zone d’accueil&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Un ou plusieurs rétrecissements (inférieurs à 80 cm) du chemin pour atteindre l'entrée"
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": True,
    },
    "accueil_prestations": {
        "is_a11y": True,
        "label": "Prestations spécifiques proposées par l'établissement",
        "help_text": mark_safe(
            "Prestations spécifiques supplémentaires proposées par l'établissement"
        ),
        "help_text_ui": None,
        "section": SECTION_ACCUEIL,
        "nullable_bool": False,
        "warn_if": None,
    },
    # Sanitaires
    "sanitaires_presence": {
        "is_a11y": True,
        "label": "Sanitaires",
        "help_text": mark_safe(
            "Y a-t-il des sanitaires mis à disposition du public&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Mise à disposition de sanitaires dans l'établissement"
        ),
        "section": SECTION_SANITAIRES,
        "nullable_bool": True,
        "warn_if": False,
    },
    "sanitaires_adaptes": {
        "is_a11y": True,
        "label": "Sanitaires adaptés",
        "help_text": mark_safe(
            "Y a-t-il des sanitaires adaptés mis à disposition du public&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Mise à disposition de sanitaires adaptés dans l'établissement"
        ),
        "section": SECTION_SANITAIRES,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x < 1,
    },
    # Labels
    "labels": {
        "is_a11y": True,
        "label": "Marques ou labels",
        "help_text": mark_safe(
            "Si l’établissement est entré dans une démarche volontaire de labellisation liée au handicap, quelle marques ou quels labels a-t-il obtenu&nbsp;?"
        ),
        "help_text_ui": mark_safe("Marque(s) ou label(s) obtenus par l'établissement"),
        "section": SECTION_LABELS,
        "nullable_bool": False,
        "warn_if": None,
    },
    "labels_familles_handicap": {
        "is_a11y": True,
        "label": "Famille(s) de handicap concernées(s)",
        "help_text": mark_safe(
            "Quelle(s) famille(s) de handicap sont couvertes par ces marques et labels&nbsp;?"
        ),
        "help_text_ui": mark_safe(
            "Famille(s) de handicap couverte(s) par ces marques ou labels"
        ),
        "section": SECTION_LABELS,
        "nullable_bool": False,
        "warn_if": None,
    },
    "labels_autre": {
        "is_a11y": True,
        "label": "Autre label",
        "help_text": mark_safe("Si autre, préciser le nom du label"),
        "help_text_ui": None,
        "section": SECTION_LABELS,
        "nullable_bool": False,
        "warn_if": None,
    },
    # Commentaire
    "commentaire": {
        "is_a11y": False,
        "label": "Commentaire libre (précisions utiles concernant l'accessibilité du bâtiment)",
        "help_text": mark_safe(
            "Indiquez ici toute information supplémentaire qui vous semble pertinente pour décrire l'accessibilité du bâtiment."
            "<br><strong>Note&nbsp;:</strong> ce commentaire sera affiché sur la fiche publique de l'établissement."
        ),
        "help_text_ui": mark_safe("Informations supplémentaires"),
        "section": SECTION_COMMENTAIRE,
        "nullable_bool": False,
        "warn_if": None,
    },
    # Registre
    "registre_url": {
        "is_a11y": False,
        "label": "Registre",
        "help_text": mark_safe(
            "Si l'établissement en dispose, adresse internet (URL) à laquelle le "
            f'<a href="{REGISTRE_INFO_URL}" target="_blank">registre d\'accessibilité</a> '
            "de l'établissement est consultable.",
        ),
        "help_text_ui": mark_safe(
            "Si l'établissement dispose d'un registre numérique, adresse internet à laquelle celui-ci est consultable",
        ),
        "section": SECTION_REGISTRE,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is None,
    },
    # Conformité
    "conformite": {
        "is_a11y": False,
        "label": "Conformité",
        "help_text": mark_safe(
            "L'établissement est-il déclaré conforme ? (réservé à l'administration)"
        ),
        "help_text_ui": mark_safe(
            "Statut réglementaire de conformité de l'établissement"
        ),
        "section": SECTION_CONFORMITE,
        "nullable_bool": True,
        "warn_if": False,
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
    #   "edit_route": "nom_de_la_route_d_edition",
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
            "edit_route": section.get("edit_route"),
            "fields": [
                dict(id=f, warn_if=FIELDS.get(f).get("warn_if"))
                for f in get_section_fields(section_id)
            ],
        }
    return fieldsets


def get_a11y_fields():
    return [key for (key, val) in FIELDS.items() if val.get("is_a11y") is True]


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


def get_help_text_ui(field):
    try:
        return FIELDS[field].get("help_text_ui")
    except KeyError:
        return None


def get_section_fields(section_id):
    return [k for (k, v) in FIELDS.items() if v["section"] == section_id]


def get_nullable_bool_fields():
    return [k for (k, v) in FIELDS.items() if v["nullable_bool"] is True]
