from django.apps import apps
from django.utils.safestring import mark_safe

from core.lib import text

# This module describes and handles accessibility fields data

UNKNOWN = "Inconnu"
UNKNOWN_OR_NA = "Inconnu ou sans objet"

BOOLEAN_CHOICES = (
    (True, "Oui"),
    (False, "Non"),
)


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
    (None, UNKNOWN),
]

EQUIPEMENT_MALENTENDANT_AUTRES = "autres"
EQUIPEMENT_MALENTENDANT_BIM = "bim"
EQUIPEMENT_MALENTENDANT_BM_PORTATIVE = "bmp"
EQUIPEMENT_MALENTENDANT_LSF = "lsf"
EQUIPEMENT_MALENTENDANT_STS = "sts"
EQUIPEMENT_MALENTENDANT_LPC = "lpc"
EQUIPEMENT_MALENTENDANT_CHOICES = [
    (EQUIPEMENT_MALENTENDANT_BIM, "boucle à induction magnétique fixe"),
    (EQUIPEMENT_MALENTENDANT_BM_PORTATIVE, "boucle à induction magnétique portative"),
    (EQUIPEMENT_MALENTENDANT_LSF, "langue des signes française (LSF)"),
    (EQUIPEMENT_MALENTENDANT_LPC, "langue française parlée complétée (LFPC)"),
    (EQUIPEMENT_MALENTENDANT_STS, "sous-titrage ou transcription simultanée"),
    (EQUIPEMENT_MALENTENDANT_AUTRES, "autres"),
]

EQUIPEMENT_MALENTENDANT_DESCRIPTIONS = {
    EQUIPEMENT_MALENTENDANT_AUTRES: "Autres équipements non précisés",
    EQUIPEMENT_MALENTENDANT_BIM: "La boucle à induction magnétique (BIM) permet d'entendre une source sonore en s'affranchissant de la distance (salles de spectacles), du bruit ambiant (lieux publics), des phénomènes d'échos ou de réverbérations sonores (églises, salles aux murs nus), des déformations apportées par les écouteurs (téléphones, MP3) ou les haut-parleurs (télévision, radio, cinéma).",
    EQUIPEMENT_MALENTENDANT_BM_PORTATIVE: "La boucle magnétique portative (BMP) est un système de transmission du son individuel",
    EQUIPEMENT_MALENTENDANT_LSF: "La langue des signes française (LSF) est la langue des signes utilisée par une partie des sourds de France et par une partie des sourds de Suisse.",
    EQUIPEMENT_MALENTENDANT_LPC: "Langue Française Parlée Complétée (LFPC)",
    EQUIPEMENT_MALENTENDANT_STS: "Service de communication, à distance et en temps réel, entre entendants et malentendants ou sourds, par sous-titrage ou transcription TIP (Transcription Instantanée de la Parole).",
}

HANDICAP_AUDITIF = "auditif"
HANDICAP_MENTAL = "mental"
HANDICAP_MOTEUR = "moteur"
HANDICAP_VISUEL = "visuel"
HANDICAP_CHOICES = [
    (HANDICAP_AUDITIF, "Handicap auditif"),
    (HANDICAP_MENTAL, "Handicap mental"),
    (HANDICAP_MOTEUR, "Handicap moteur"),
    (HANDICAP_VISUEL, "Handicap visuel"),
]

DISPOSITIFS_APPEL_BOUTON = "bouton"
DISPOSITIFS_APPEL_INTERPHONE = "interphone"
DISPOSITIFS_APPEL_VISIOPHONE = "visiophone"
DISPOSITIFS_APPEL_CHOICES = [
    (DISPOSITIFS_APPEL_BOUTON, "Bouton d'appel"),
    (DISPOSITIFS_APPEL_INTERPHONE, "Interphone"),
    (DISPOSITIFS_APPEL_VISIOPHONE, "Visiophone"),
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

PENTE_LEGERE = "légère"
PENTE_IMPORTANTE = "importante"
PENTE_CHOICES = [
    (PENTE_LEGERE, "Légère"),
    (PENTE_IMPORTANTE, "Importante"),
    (None, UNKNOWN),
]

PENTE_LONGUEUR_COURTE = "courte"
PENTE_LONGUEUR_MOYENNE = "moyenne"
PENTE_LONGUEUR_LONGUE = "longue"
PENTE_LENGTH_CHOICES = [
    (PENTE_LONGUEUR_COURTE, "< 0,5 mètres"),
    (PENTE_LONGUEUR_MOYENNE, "entre 0,5 et 2 mètres"),
    (PENTE_LONGUEUR_LONGUE, "> 2 mètres"),
    (None, UNKNOWN),
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

PORTE_TYPE_MANUELLE = "manuelle"
PORTE_TYPE_AUTOMATIQUE = "automatique"
PORTE_TYPE_CHOICES = [
    (PORTE_TYPE_MANUELLE, "Manuelle"),
    (PORTE_TYPE_AUTOMATIQUE, "Automatique"),
    (None, UNKNOWN_OR_NA),
]

PORTE_MANOEUVRE_BATTANTE = "battante"
PORTE_MANOEUVRE_COULISSANTE = "coulissante"
PORTE_MANOEUVRE_TOURNIQUET = "tourniquet"
PORTE_MANOEUVRE_TAMBOUR = "tambour"
PORTE_MANOEUVRE_CHOICES = [
    (PORTE_MANOEUVRE_BATTANTE, "Porte battante"),
    (PORTE_MANOEUVRE_COULISSANTE, "Porte coulissante"),
    (PORTE_MANOEUVRE_TOURNIQUET, "Tourniquet"),
    (PORTE_MANOEUVRE_TAMBOUR, "Porte tambour"),
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

ESCALIER_MONTANT = "montant"
ESCALIER_DESCENDANT = "descendant"
ESCALIER_SENS = [
    (ESCALIER_MONTANT, "Montant"),
    (ESCALIER_DESCENDANT, "Descendant"),
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
        "short_description": "Expert en données d'accessibilité",
        "template": "editorial/partenaires/wegoto.html",
        "url": "https://www.wegoto.eu/",
    },
    "ACCESMETRIE": {
        "avatar": "accesmetrie_avatar.png",
        "logo": "img/partenaires/accesmetrie.jpg",
        "name": "AccèsMétrie",
        "short_description": "Expert en données d'accessibilité",
        "template": "editorial/partenaires/accesmetrie.html",
        "url": "http://www.accesmetrie.com",
    },
    "ONECOMPAGNON": {
        "avatar": "onecompagnon_avatar.jpg",
        "logo": "img/partenaires/onecompagnon.png",
        "name": "One Compagnon",
        "short_description": "L'assitant accessible à tous",
        "template": "editorial/partenaires/onecompagnon.html",
        "url": "https://www.onecompagnon.com",
    },
    "SORTIRAPARIS": {
        "avatar": "sortir-a-paris_avatar.png",
        "logo": "img/partenaires/sap.png",
        "name": "Sortir À Paris",
        "short_description": "1er média d'actualité Sorties en France",
        "template": "editorial/partenaires/sortiraparis.html",
        "url": "https://www.sortiraparis.com",
    },
    "NESTENN": {
        "avatar": "nestenn_avatar.png",
        "logo": "img/partenaires/nestenn.png",
        "name": "Nestenn",
        "short_description": "Groupe d'agences immobilières",
        "template": "editorial/partenaires/nestenn.html",
        "url": "https://nestenn.com/groupe-immobilier-nestenn",
    },
    "ANDRE_DE_CABO": {
        "avatar": "andre_cabo_avatar.jpg",
        "logo": "img/partenaires/andre_cabo.jpg",
        "name": "André de CABO",
        "short_description": "Notre vocation est de vous conseiller et de vous accompagner",
        "template": "editorial/partenaires/andre_de_cabo.html",
        "url": "https://andredecabo.fr/",
    },
}

SECTION_A_PROPOS = "a_propos"
SECTION_TRANSPORT = "transport"
SECTION_STATIONNEMENT = "stationnement"
SECTION_CHEMINEMENT_EXT = "cheminement_ext"
SECTION_ENTREE = "entree"
SECTION_ACCUEIL = "accueil"
SECTION_SANITAIRES = "sanitaires"
SECTION_LABELS = "labels"
SECTION_REGISTRE = "registre"
SECTION_CONFORMITE = "conformite"
SECTION_ACTIVITE = "activite"
SECTION_COMMENTAIRE = "commentaire"
SECTIONS = {
    SECTION_A_PROPOS: {
        "icon": "trophy",
        "label": "À propos",
        "description": "de l'établissement",
        "edit_route": "contrib_a_propos",
    },
    SECTION_TRANSPORT: {
        "icon": "bus",
        "label": "Accès",
        "description": "à proximité",
        "edit_route": "contrib_transport",
    },
    SECTION_STATIONNEMENT: {
        "icon": "car",
        "label": "Stationnement",
        "description": "aux abords de l'établissement",
        "edit_route": "contrib_stationnement",
    },
    SECTION_CHEMINEMENT_EXT: {
        "icon": "road",
        "label": "Chemin extérieur",
        "description": "depuis la voirie jusqu'à l'entrée",
        "edit_route": "contrib_exterieur",
    },
    SECTION_ENTREE: {
        "icon": "entrance",
        "label": "Entrée",
        "description": "de l'établissement",
        "edit_route": "contrib_entree",
    },
    SECTION_ACCUEIL: {
        "icon": "users",
        "label": "Accueil",
        "description": "et prestations",
        "edit_route": "contrib_accueil",
    },
    SECTION_SANITAIRES: {
        "icon": "male-female",
        "label": "Sanitaires",
        "description": "Toilettes, WC",
        "edit_route": "contrib_sanitaires",
    },
    SECTION_REGISTRE: {
        "icon": "registre",
        "label": "Registre",
        "description": "d'accessibilité de l'établissement",
        "edit_route": None,
    },
    SECTION_CONFORMITE: {
        "icon": "conformite",
        "label": "Conformité",
        "description": "à la règlementation",
        "edit_route": None,
    },
    SECTION_COMMENTAIRE: {
        "icon": "info-circled",
        "label": "Commentaire",
        "description": "et informations complémentaires",
        "edit_route": "contrib_commentaire",
    },
}

FIELDS = {
    # Transport
    "transport_station_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Proximité d'un arrêt de transport en commun",
        "help_text": mark_safe(
            "Existe-t-il un arrêt de transport en commun à moins de 200 mètres de l'établissement&nbsp;?"
        ),
        "help_text_ui": "Arrêt de transport en commun à moins de 200 mètres de l'établissement",
        "help_text_ui_neg": "Pas d'arrêt de transport en commun à moins de 200 mètres de l'établissement",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_TRANSPORT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "transport_information": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Informations complémentaires",
        "help_text": mark_safe(
            "Préciser ici les informations supplémentaires sur ces transports (type de transport, ligne, nom de l'arrêt, etc) et éventuellement des informations jugées importantes sur le chemin qui relie le point d'arrêt à l'établissement."
        ),
        "help_text_ui": "Informations sur l'accessibilité par les transports en commun",
        "help_text_ui_neg": "Informations sur l'accessibilité par les transports en commun",
        "choices": None,
        "section": SECTION_TRANSPORT,
        "nullable_bool": False,
        "warn_if": None,
        "example": "Ligne n4",
    },
    # Stationnement
    "stationnement_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Stationnement dans l'établissement",
        "help_text": mark_safe(
            "Existe-t-il une ou plusieurs places de stationnement dans l'établissement ou au sein de la parcelle de l'établissement&nbsp;?"
        ),
        "help_text_ui": "Des places de stationnement sont disponibles au sein de la parcelle de l'établissement",
        "help_text_ui_neg": "Pas de place de stationnement disponible au sein de la parcelle de l'établissement",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_TRANSPORT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "stationnement_pmr": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Stationnements adaptés dans l'établissement",
        "help_text": mark_safe(
            "Existe-t-il une ou plusieurs places de stationnement adaptées dans l'établissement ou au sein de la parcelle de l'établissement&nbsp;?"
        ),
        "help_text_ui": "Des places de stationnement adaptées sont disponibles au sein de la parcelle de l'établissement",
        "help_text_ui_neg": "Pas de place de stationnement disponible adaptée au sein de la parcelle de l'établissement",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_TRANSPORT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "stationnement_ext_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Stationnement à proximité de l'établissement",
        "help_text": mark_safe(
            "Existe-t-il une ou plusieurs places de stationnement en voirie ou en parking à moins de 200 mètres de l'établissement&nbsp;?"
        ),
        "help_text_ui": "Des places de stationnement sont disponibles à moins de 200 mètres de l'établissement",
        "help_text_ui_neg": "Pas de place de stationnement disponible à moins de 200 mètres de l'établissement",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_TRANSPORT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "stationnement_ext_pmr": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Stationnements adaptés à proximité de l'établissement",
        "help_text": mark_safe(
            "Existe-t-il une ou plusieurs places de stationnement adaptées en voirie ou en parking à moins de 200 mètres de l'établissement&nbsp;?"
        ),
        "help_text_ui": "Des places de stationnement adaptées sont disponibles à moins de 200 mètres de l'établissement",
        "help_text_ui_neg": "Pas de place de stationnement disponible adaptée à moins de 200 mètres de l'établissement",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_TRANSPORT,
        "nullable_bool": True,
        "warn_if": False,
    },
    # Cheminement extérieur
    "cheminement_ext_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Chemin extérieur",
        "help_text": mark_safe(
            "Y-a-t-il un chemin extérieur entre le trottoir et l'entrée principale du bâtiment (exemple&nbsp;: une cour)&nbsp;?"
        ),
        "help_text_ui": "L'accès à l'entrée depuis la voirie se fait par un chemin extérieur",
        "help_text_ui_neg": "Pas de chemin extérieur entre le trottoir et l'entrée principale du bâtiment",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": True,
    },
    "cheminement_ext_terrain_stable": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Revêtement extérieur",
        "help_text": mark_safe(
            "Le revêtement du chemin extérieur (entre le trottoir et l'entrée de l'établissement) est-il stable (sol roulable, absence de pavés ou de gravillons, pas de terre ni d'herbe, etc.)&nbsp;?"
        ),
        "help_text_ui": "Le revêtement est stable (absence de pavés, gravillons, terre, herbe, sable, ou toute surface non stabilisée)",
        "help_text_ui_neg": "Le revêtement n'est pas stable (pavés, gravillons, terre, herbe, sable, ou toute surface non stabilisée)",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_plain_pied": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Chemin extérieur de plain-pied",
        "help_text": mark_safe(
            "Le chemin est-il de plain-pied, c'est-à-dire sans marche ni ressaut supérieur à 2 centimètres&nbsp;? "
            "Attention plain-pied ne signifie pas plat mais sans rupture brutale de niveau."
        ),
        "help_text_ui": "L'accès à cet espace se fait de plain-pied, c'est à dire sans rupture brutale de niveau",
        "help_text_ui_neg": "L'accès à cet espace n'est pas de plain-pied et présente une rupture brutale de niveau",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_ascenseur": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Ascenseur/élévateur",
        "help_text": mark_safe("Existe-t-il un ascenseur ou un élévateur&nbsp;?"),
        "help_text_ui": "Présence d'un ascenseur ou un élévateur",
        "help_text_ui_neg": "Pas d'ascenseur ou d'élévateur",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
        "description": "Existe-t-il un ascenseur ou un élévateur&nbsp;?",
    },
    "cheminement_ext_nombre_marches": {
        "type": "number",
        "nullable": True,
        "is_a11y": True,
        "label": "Nombre de marches",
        "help_text": mark_safe("Indiquer 0 s'il n'y a ni marche ni escalier"),
        "help_text_ui": "Nombre de marches de l'escalier",
        "help_text_ui_neg": "Aucune marche d'escalier",
        "section": SECTION_CHEMINEMENT_EXT,
        "choices": None,
        "unit": "marche",
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x > 0,
        "description": "Combien y'a t'il de marches&nbsp;?",
    },
    "cheminement_ext_sens_marches": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Sens de circulation de l'escalier",
        "help_text": mark_safe(
            "Quel est le sens de circulation des marches ou de l'escalier&nbsp;?"
        ),
        "help_text_ui": "Sens de circulation des marches ou de l'escalier",
        "help_text_ui_neg": "Sens de circulation des marches ou de l'escalier",
        "choices": ESCALIER_SENS,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": None,
    },
    "cheminement_ext_reperage_marches": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Marches ou escalier sécurisé(es)",
        "help_text": mark_safe(
            "L'escalier est-il sécurisé&nbsp;: nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées&nbsp;?"
        ),
        "help_text_ui": "Présence de nez de marche contrastés, d'une bande d'éveil à la vigilance en haut de l'escalier et/ou de première et dernière contremarches contrastées",
        "help_text_ui_neg": "Pas de nez de marche contrasté, de bande d'éveil à la vigilance en haut de l'escalier ni de première et dernière contremarches contrastées",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_main_courante": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Main courante",
        "help_text": mark_safe(
            "L'escalier est-il équipé d'une ou plusieurs main-courantes&nbsp;?"
        ),
        "help_text_ui": "L'escalier est équipé d'une ou plusieurs main-courantes",
        "help_text_ui_neg": "L'escalier n'est pas équipé de main-courante",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_rampe": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Rampe",
        "help_text": mark_safe(
            "S'il existe une rampe ayant une pente douce, est-elle fixe ou amovible&nbsp;?"
        ),
        "help_text_ui": "Présence d'une rampe fixe ou amovible",
        "help_text_ui_neg": "Pas de rampe fixe ou amovible",
        "choices": RAMPE_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": RAMPE_AUCUNE,
    },
    "cheminement_ext_pente_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Pente",
        "help_text": mark_safe("Le chemin est-il en pente&nbsp;?"),
        "help_text_ui": "Le chemin est en pente",
        "help_text_ui_neg": "Le chemin n'est pas en pente",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": True,
    },
    "cheminement_ext_pente_degre_difficulte": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Degré de difficulté de la pente",
        "help_text": mark_safe("Quel est son degré de difficulté&nbsp;?"),
        "help_text_ui": "Difficulté de la pente",
        "help_text_ui_neg": "Difficulté de la pente",
        "choices": PENTE_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None and x in [PENTE_LEGERE, PENTE_IMPORTANTE],
    },
    "cheminement_ext_pente_longueur": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Longueur de la pente",
        "help_text": mark_safe("Longueur de la pente"),
        "help_text_ui": "Longueur de la pente",
        "choices": PENTE_LENGTH_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None
        and x in [PENTE_LONGUEUR_MOYENNE, PENTE_LONGUEUR_LONGUE],
    },
    "cheminement_ext_devers": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Dévers",
        "help_text": mark_safe(
            "Un dévers est une inclinaison transversale du chemin. S'il en existe un, quel est son degré de difficulté&nbsp;?"
        ),
        "help_text_ui": "Dévers ou inclinaison transversale du chemin",
        "help_text_ui_neg": "Pas de dévers ou d'inclinaison transversale du chemin",
        "choices": DEVERS_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None and x in [DEVERS_LEGER, DEVERS_IMPORTANT],
    },
    "cheminement_ext_bande_guidage": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Bande de guidage",
        "help_text": mark_safe(
            "Présence d'une bande de guidage au sol facilitant le déplacement d'une personne aveugle ou malvoyante"
        ),
        "help_text_ui": "Présence d'une bande de guidage au sol facilitant le déplacement d'une personne aveugle ou malvoyante",
        "help_text_ui_neg": "Pas de bande de guidage au sol facilitant le déplacement d'une personne aveugle ou malvoyante",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_retrecissement": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Rétrécissement du chemin",
        "help_text": mark_safe(
            "Existe-t-il un ou plusieurs rétrécissements (inférieur à 90 centimètres) du chemin emprunté par le public pour atteindre l'entrée&nbsp;?"
        ),
        "help_text_ui": "Un ou plusieurs rétrécissements inférieurs à 90 centimètres du chemin pour atteindre la zone d'accueil",
        "help_text_ui_neg": "Pas de rétrécissement inférieur à 90 centimètres du chemin pour atteindre la zone d'accueil",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": True,
    },
    # Entrée
    "entree_reperage": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Entrée facilement repérable",
        "help_text": mark_safe(
            "Y a-t-il des éléments facilitant le repérage de l'entrée de l'établissement (numéro de rue à proximité, enseigne, végétaux, éléments architecturaux contrastés, etc)&nbsp;?"
        ),
        "help_text_ui": "L'entrée de l'établissement est facilement repérable",
        "help_text_ui_neg": "Pas d'éléments facilitant le repérage de l'entrée de l'établissement (numéro de rue à proximité, enseigne, végétaux, éléments architecturaux contrastés, etc)",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_porte_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Y a-t-il une porte ?",
        "help_text": mark_safe(
            "Y a-t-il une porte à l'entrée de l'établissement&nbsp;?"
        ),
        "help_text_ui": "Présence d'une porte à l'entrée de l'établissement",
        "help_text_ui_neg": "Pas de porte à l'entrée de l'établissement",
        "choices": BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": None,
        "required": True,
    },
    "entree_porte_manoeuvre": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Manoeuvre de la porte",
        "help_text": mark_safe("Comment s'ouvre la porte&nbsp;?"),
        "help_text_ui": "Mode d'ouverture de la porte",
        "help_text_ui_neg": "Mode d'ouverture de la porte",
        "choices": PORTE_MANOEUVRE_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": None,
    },
    "entree_porte_type": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Type de porte",
        "help_text": mark_safe("Quel est le type de la porte&nbsp;?"),
        "help_text_ui": "Type de porte",
        "help_text_ui_neg": "Type de porte",
        "choices": PORTE_TYPE_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": None,
    },
    "entree_vitree": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Entrée vitrée",
        "help_text": mark_safe("La porte d'entrée est-elle vitrée&nbsp;?"),
        "help_text_ui": "La porte d'entrée est vitrée",
        "help_text_ui_neg": "La porte d'entrée n'est pas vitrée",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": True,
    },
    "entree_vitree_vitrophanie": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Repérage de la vitre",
        "help_text": mark_safe(
            "Y a-t-il des éléments contrastés (autocollants, éléments de menuiserie ou autres) permettant de repérer la porte vitrée&nbsp;?"
        ),
        "help_text_ui": "Des éléments contrastés permettent de visualiser les parties vitrées de l'entrée",
        "help_text_ui_neg": "Pas d'éléments contrastés permettant de visualiser les parties vitrées de l'entrée",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_plain_pied": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Entrée de plain-pied",
        "help_text": mark_safe(
            "L'entrée est-elle de plain-pied, c'est-à-dire sans marche ni ressaut supérieur à 2 centimètres&nbsp;?"
        ),
        "help_text_ui": "L'entrée se fait de plain-pied, c'est à dire sans rupture brutale de niveau",
        "help_text_ui_neg": "L'entrée n'est pas de plain-pied et présente une rupture brutale de niveau",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_ascenseur": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Ascenseur/élévateur",
        "help_text": mark_safe("Existe-t-il un ascenseur ou un élévateur&nbsp;?"),
        "help_text_ui": "Présence d'un ascenseur ou d'un élévateur",
        "help_text_ui_neg": "Pas d'ascenseur ou d'élévateur",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_marches": {
        "type": "number",
        "nullable": True,
        "is_a11y": True,
        "label": "Nombre de marches",
        "help_text": mark_safe("Indiquer 0 s'il n'y a ni marche ni escalier"),
        "help_text_ui": "Nombre de marches de l'escalier",
        "help_text_ui_neg": "Pas de marches d'escalier",
        "choices": None,
        "unit": "marche",
        "section": SECTION_ENTREE,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x > 0,
    },
    "entree_marches_sens": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Sens de circulation de l'escalier",
        "help_text": mark_safe(
            "Quel est le sens de circulation des marches ou de l'escalier&nbsp;?"
        ),
        "help_text_ui": "Sens de circulation des marches ou de l'escalier",
        "help_text_ui_neg": "Sens de circulation des marches ou de l'escalier",
        "choices": ESCALIER_SENS,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": None,
    },
    "entree_marches_reperage": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Repérage des marches",
        "help_text": mark_safe(
            "L'escalier est-il sécurisé&nbsp;: nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées&nbsp;?"
        ),
        "help_text_ui": "Présence de nez de marche contrastés, d'une bande d'éveil à la vigilance en haut de l'escalier et/ou de première et dernière contremarches contrastées",
        "help_text_ui_neg": "Pas de nez de marche contrasté, de bande d'éveil à la vigilance en haut de l'escalier ni de première et dernière contremarches contrastées",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_marches_main_courante": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Main courante",
        "help_text": mark_safe(
            "L'escalier est-il équipé d'une ou plusieurs main-courantes&nbsp;?"
        ),
        "help_text_ui": "L'escalier est équipé d'une ou plusieurs main-courantes",
        "help_text_ui_neg": "L'escalier n'est pas équipé de main-courante",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_marches_rampe": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Rampe",
        "help_text": mark_safe(
            "S'il existe une rampe ayant une pente douce, est-elle fixe ou amovible&nbsp;?"
        ),
        "help_text_ui": "Présence d'une rampe fixe ou amovible",
        "help_text_ui_neg": "Pas de rampe fixe ou amovible",
        "choices": RAMPE_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is False or x == RAMPE_AUCUNE,
    },
    "entree_dispositif_appel": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Dispositif d'appel à l'entrée",
        "help_text": mark_safe(
            "Existe-t-il un dispositif pour permettre à quelqu'un signaler sa présence à l'entrée&nbsp;?"
        ),
        "help_text_ui": "Présence d'un dispositif comme une sonnette pour signaler sa présence",
        "help_text_ui_neg": "Pas de dispositif comme une sonnette pour signaler sa présence",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_dispositif_appel_type": {
        "type": "array",
        "nullable": True,
        "is_a11y": True,
        "label": "Type de dispositif d'appel à l'entrée",
        "help_text": mark_safe(
            "Quel(s) type(s) de dispositifs d'appel sont présents&nbsp;?"
        ),
        "help_text_ui": "Dispositifs d'appels présents",
        "help_text_ui_neg": "Dispositifs d'appels présents",
        "choices": DISPOSITIFS_APPEL_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_balise_sonore": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Balise sonore à l'entrée",
        "help_text": mark_safe(
            "L'entrée est-elle équipée d'une balise sonore facilitant son repérage par une personne aveugle ou malvoyante&nbsp;?"
        ),
        "help_text_ui": "Présence d'une balise sonore facilitant son repérage par une personne aveugle ou malvoyante",
        "help_text_ui_neg": "Pas de balise sonore facilitant son repérage par une personne aveugle ou malvoyante",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_aide_humaine": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Aide humaine",
        "help_text": mark_safe(
            "Présence ou possibilité d'une aide humaine au déplacement"
        ),
        "help_text_ui": "Possibilité d'une aide humaine au déplacement",
        "help_text_ui_neg": "Pas de possibilité d'aide humaine au déplacement",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_largeur_mini": {
        "type": "number",
        "nullable": True,
        "is_a11y": True,
        "label": "Largeur de la porte",
        "help_text": mark_safe(
            "Si la largeur n'est pas précisément connue, indiquer une valeur minimum. Exemple&nbsp;: la largeur se situe entre 90 et 100 centimètres&nbsp;; indiquer 90."
        ),
        "help_text_ui": "Largeur minimale de la porte d'entrée",
        "help_text_ui_neg": "Largeur minimale de la porte d'entrée",
        "choices": None,
        "unit": "centimètre",
        "section": SECTION_ENTREE,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x < 80,
    },
    "entree_pmr": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Entrée spécifique PMR",
        "help_text": mark_safe(
            "Existe-t-il une entrée secondaire spécifique dédiée aux personnes à mobilité réduite&nbsp;?"
        ),
        "help_text_ui": "Présence d'une entrée secondaire spécifique dédiée aux personnes à mobilité réduite",
        "help_text_ui_neg": "Pas d'entrée secondaire spécifique dédiée aux personnes à mobilité réduite",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_pmr_informations": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Informations complémentaires concernant l'entrée PMR",
        "help_text": mark_safe(
            "Précisions sur les modalités d'accès de l'entrée spécifique PMR"
        ),
        "help_text_ui": "Précisions sur les modalités d'accès de l'entrée spécifique PMR",
        "help_text_ui_neg": "Précisions sur les modalités d'accès de l'entrée spécifique PMR",
        "choices": None,
        "section": SECTION_ENTREE,
        "nullable_bool": False,
        "warn_if": None,
        "example": "Entrée fléchée",
    },
    # Accueil
    "accueil_visibilite": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Visibilité de la zone d'accueil",
        "help_text": mark_safe(
            "La zone d'accueil (guichet d'accueil, caisse, secrétariat, etc) est-elle visible depuis l'entrée du bâtiment&nbsp;?"
        ),
        "help_text_ui": "La zone d'accueil (guichet d'accueil, caisse, secrétariat, etc) est visible depuis l'entrée du bâtiment",
        "help_text_ui_neg": "La zone d'accueil (guichet d'accueil, caisse, secrétariat, etc) n'est pas visible depuis l'entrée du bâtiment",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_plain_pied": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Chemin entre l'entrée principale du bâtiment et l'accueil de l'établissement",
        "help_text": mark_safe(
            "Une fois l'entrée du bâtiment passée, le chemin jusqu'à l'accueil de l'établissement "
            "est t-il de plain-pied, c'est-à-dire sans marche ni ressaut supérieur à 2 centimètres&nbsp;? "
            "(attention, plain-pied ne signifie pas plat mais sans rupture brutale de niveau)"
        ),
        "help_text_ui": "L'accès à cet espace se fait de plain-pied, c'est à dire sans rupture brutale de niveau",
        "help_text_ui_neg": "L'accès à cet espace n'est pas de plain-pied et présente une rupture brutale de niveau",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_ascenseur": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Ascenseur/élévateur",
        "help_text": mark_safe("Existe-t-il un ascenseur ou un élévateur&nbsp;?"),
        "help_text_ui": "Présence d'un ascenseur ou un élévateur",
        "help_text_ui_neg": "Pas d'ascenseur ou d'élévateur",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_nombre_marches": {
        "type": "number",
        "nullable": True,
        "is_a11y": True,
        "label": "Nombre de marches",
        "help_text": mark_safe("Indiquer 0 s'il n'y a ni marche ni escalier"),
        "help_text_ui": "Nombre de marches de l'escalier",
        "help_text_ui_neg": "Pas de marches d'escalier",
        "choices": None,
        "unit": "marche",
        "section": SECTION_ACCUEIL,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x > 0,
    },
    "accueil_cheminement_sens_marches": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Sens de circulation de l'escalier",
        "help_text": mark_safe(
            "Quel est le sens de circulation des marches ou de l'escalier&nbsp;?"
        ),
        "help_text_ui": "Sens de circulation des marches ou de l'escalier",
        "help_text_ui_neg": "Sens de circulation des marches ou de l'escalier",
        "choices": ESCALIER_SENS,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": None,
    },
    "accueil_cheminement_reperage_marches": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Repérage des marches ou de l'escalier",
        "help_text": mark_safe(
            "L'escalier est-il sécurisé&nbsp;: nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées&nbsp;?"
        ),
        "help_text_ui": "Nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier et/ou première et dernière contremarches contrastées",
        "help_text_ui_neg": "Pas de nez de marche contrasté, de bande d'éveil à la vigilance en haut de l'escalier ni de première et dernière contremarches contrastées",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_main_courante": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Main courante",
        "help_text": mark_safe(
            "L'escalier est-il équipé d'une ou plusieurs main-courantes&nbsp;?"
        ),
        "help_text_ui": "L'escalier est équipé d'une ou plusieurs main-courantes",
        "help_text_ui_neg": "L'escalier n'est pas équipé de main-courante",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_rampe": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Rampe",
        "help_text": mark_safe(
            "S'il existe une rampe ayant une pente douce, est-elle fixe ou amovible&nbsp;?"
        ),
        "help_text_ui": "Présence d'une rampe fixe ou amovible",
        "help_text_ui_neg": "Pas de rampe fixe ou amovible",
        "choices": RAMPE_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_retrecissement": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Rétrécissement du chemin",
        "help_text": mark_safe(
            "Existe-t-il un ou plusieurs rétrécissements (inférieur à 90 centimètres) du chemin emprunté par le public pour atteindre la zone d'accueil&nbsp;?"
        ),
        "help_text_ui": "Présence d'un ou plusieurs rétrécissements inférieurs à 90 centimètres du chemin pour atteindre la zone d'accueil",
        "help_text_ui_neg": "Pas de rétrécissement inférieur à 90 centimètres du chemin pour atteindre la zone d'accueil",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": True,
    },
    "accueil_personnels": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Personnel d'accueil",
        "help_text": mark_safe(
            "En cas de présence du personnel, est-il formé ou sensibilisé à l'accueil des personnes handicapées&nbsp;?"
        ),
        "help_text_ui": "Personnel à l'accueil des personnes handicapées",
        "help_text_ui_neg": "Aucun personnel à l'accueil des personnes handicapées",
        "choices": PERSONNELS_CHOICES,
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
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Présence d'équipements d'aide à l'audition et à la communication",
        "help_text": mark_safe(
            "L'accueil est-il équipé de produits ou prestations dédiés aux personnes sourdes ou malentendantes&nbsp?"
        ),
        "help_text_ui": "Présence de produits ou prestations dédiés aux personnes sourdes ou malentendantes",
        "help_text_ui_neg": "Pas de produits ou prestations dédiés aux personnes sourdes ou malentendantes",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_equipements_malentendants": {
        "type": "array",
        "nullable": False,
        "is_a11y": True,
        "label": "Liste des équipements d'aide à l'audition et à la communication",
        "help_text": mark_safe(
            "Sélectionnez les équipements ou prestations disponibles à l'accueil de l'établissement&nbsp;:"
        ),
        "help_text_ui": "Équipements ou prestations disponibles",
        "help_text_ui_neg": "Équipements ou prestations disponibles",
        "choices": EQUIPEMENT_MALENTENDANT_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None and len(x) == 0,
    },
    # Sanitaires
    "sanitaires_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Sanitaires",
        "help_text": mark_safe(
            "Y a-t-il des sanitaires mis à disposition du public&nbsp;?"
        ),
        "help_text_ui": "Des sanitaires sont mis à disposition dans l'établissement",
        "help_text_ui_neg": "Pas de sanitaires mis à disposition dans l'établissement",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "sanitaires_adaptes": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": "Sanitaires adaptés",
        "help_text": mark_safe(
            "Y a-t-il des sanitaires adaptés mis à disposition du public&nbsp;?"
        ),
        "help_text_ui": "Des sanitaires adaptés sont mis à disposition dans l'établissement",
        "help_text_ui_neg": "Aucun sanitaire adapté mis à disposition dans l'établissement",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    # Labels
    "labels": {
        "type": "array",
        "nullable": False,
        "is_a11y": True,
        "label": "Marques ou labels",
        "help_text": mark_safe(
            "Si l'établissement est entré dans une démarche volontaire de labellisation liée au handicap, quelle marque ou quel label a-t-il obtenu(e)&nbsp;?"
        ),
        "help_text_ui": "Marque(s) ou label(s) obtenus par l'établissement",
        "help_text_ui_neg": "Marque(s) ou label(s) obtenus par l'établissement",
        "choices": LABEL_CHOICES,
        "section": SECTION_COMMENTAIRE,
        "nullable_bool": False,
        "warn_if": None,
    },
    "labels_familles_handicap": {
        "type": "array",
        "nullable": False,
        "is_a11y": True,
        "label": "Famille(s) de handicap concernées(s)",
        "help_text": mark_safe(
            "Quelle(s) famille(s) de handicap sont couvertes par ces marques et labels&nbsp;?"
        ),
        "help_text_ui": "Famille(s) de handicap couverte(s) par ces marques ou labels",
        "help_text_ui_neg": "Famille(s) de handicap couverte(s) par ces marques ou labels",
        "choices": HANDICAP_CHOICES,
        "section": SECTION_COMMENTAIRE,
        "nullable_bool": False,
        "warn_if": None,
    },
    "labels_autre": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": "Autre label",
        "help_text": mark_safe("Si autre, préciser le nom du label"),
        "help_text_ui": "Autre marque ou label obtenus",
        "help_text_ui_neg": "Autre marque ou label obtenus",
        "choices": None,
        "section": SECTION_COMMENTAIRE,
        "nullable_bool": False,
        "warn_if": None,
        "example": "HandiLabel",
    },
    # Commentaire
    "commentaire": {
        "type": "string",
        "nullable": True,
        "is_a11y": False,
        "label": mark_safe(
            "<strong>Informations complémentaires et prestations spécifiques</strong>"
        ),
        "help_text": mark_safe(
            "Ajoutez ici toute information supplémentaire concernant l'accessibilité du bâtiment ou des prestations spécifiques proposées."
        ),
        "help_text_ui": "Informations supplémentaires concernant l'accessibilité du bâtiment ou des prestations spécifiques proposées",
        "help_text_ui_neg": "Informations supplémentaires concernant l'accessibilité du bâtiment ou des prestations spécifiques proposées",
        "choices": None,
        "section": SECTION_COMMENTAIRE,
        "nullable_bool": False,
        "warn_if": None,
        "example": "Propose des places gratuites",
    },
    # Registre
    "registre_url": {
        "type": "string",
        "nullable": True,
        "is_a11y": False,
        "label": "Registre",
        "help_text": mark_safe(
            "Si l'établissement en dispose, adresse internet (URL) à laquelle le "
            f'<a href="{REGISTRE_INFO_URL}" target="_blank">registre d\'accessibilité</a> '
            "de l'établissement est consultable.",
        ),
        "help_text_ui": "Adresse internet à laquelle le registre est consultable",
        "help_text_ui_neg": "Adresse internet à laquelle le registre est consultable",
        "section": SECTION_REGISTRE,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is None,
        "example": f"{REGISTRE_INFO_URL}",
    },
    # Conformité
    "conformite": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": False,
        "label": "Conformité",
        "help_text": mark_safe(
            "L'établissement est-il déclaré conforme ? (réservé à l'administration)"
        ),
        "help_text_ui": "L'établissement a été déclaré conforme à la réglementation",
        "help_text_ui_neg": "l'établissement n'a pas été déclaré conforme à la réglementation auprès de l'administration",
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_CONFORMITE,
        "nullable_bool": True,
        "warn_if": False,
    },
    # Activité
    "activite": {
        "type": "string",
        "nullable": False,
        "is_a11y": False,
        "label": "Activité",
        "help_text": mark_safe("Domaine d'activité de l'ERP"),
        "help_text_ui": "Domaine d'activité de l'ERP",
        "help_text_ui_neg": "Domaine d'activité de l'ERP",
        "app_model": ("erp", "Activite"),
        "attribute": "nom",
        "nullable_bool": True,
        "section": SECTION_ACTIVITE,
    },
}

# Fix me : write additional documentation


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


def get_documentation_fieldsets():
    # {"Nom de la section": {
    #   "fields": [
    #     {"label": "Nom du champ",
    #      "type": "type de champ",
    #      ""
    #      }
    #   ],
    # },
    fieldsets = {}
    for section_id, section in SECTIONS.items():
        fields = []
        for field_id in get_section_fields(section_id):
            fields.append(FIELDS.get(field_id))
        fieldsets[section["label"]] = fields

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
                dict(
                    id=f,
                    choices=FIELDS.get(f).get("choices"),
                    unit=FIELDS.get(f).get("unit"),
                    warn_if=FIELDS.get(f).get("warn_if"),
                )
                for f in get_section_fields(section_id)
            ],
        }
    return fieldsets


def get_a11y_fields():
    return [key for (key, val) in FIELDS.items() if val.get("is_a11y") is True]


def get_bdd_values(field):
    try:
        field = FIELDS.get(field)
        return (
            apps.get_model(*field.get("app_model"))
            .objects.all()
            .values_list(field.get("attribute"), flat=True)
        )
    except AttributeError:
        return None


def get_field_choices(field):
    try:
        return FIELDS.get(field).get("choices")
    except AttributeError:
        return None


def get_human_readable_value(field, value):
    """
    returns : (str) human readable value for this field.
    """
    return text.humanize_value(value, choices=get_field_choices(field))


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


def get_help_text_ui_neg(field):
    try:
        return FIELDS[field].get("help_text_ui_neg") or get_help_text_ui(field)
    except KeyError:
        return get_help_text_ui(field)


def get_nullable(field):
    return FIELDS[field].get("nullable")


def get_nullable_bool_fields():
    return [k for (k, v) in FIELDS.items() if v["nullable_bool"] is True]


def get_required_fields():
    return [k for (k, v) in FIELDS.items() if "required" in v and v["required"] is True]


def get_section_fields(section_id):
    return [k for (k, v) in FIELDS.items() if v["section"] == section_id]


def get_type(field):
    return FIELDS[field].get("type")
