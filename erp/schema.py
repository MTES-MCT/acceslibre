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

REGISTRE_INFO_URL = "https://handicap.gouv.fr/actualites/article/registre-d-accessibilite-obligatoire-un-guide-pour-les-erp"

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
    SECTION_REGISTRE: {
        "icon": "registre",
        "label": "Registre",
        "description": "Registre d'accessibilité de l'établissement",
    },
    SECTION_CONFORMITE: {
        "icon": "conformite",
        "label": "Conformité",
        "description": "Conformité",
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
        "is_a11y": True,
        "label": "Desserte par transports en commun",
        "help_text": mark_safe(
            "L'établissement est-il desservi par les transports en commun&nbsp;?"
        ),
        "section": SECTION_TRANSPORT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "transport_information": {
        "is_a11y": True,
        "label": "Informations transports",
        "help_text": mark_safe(
            "Préciser ici les informations supplémentaires sur ces transports (type de transport, ligne, nom de l'arrêt, etc) et éventuellement des informations jugées importantes sur le cheminement qui relie le point d'arrêt à l'établissement."
        ),
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
        "section": SECTION_STATIONNEMENT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "stationnement_pmr": {
        "is_a11y": True,
        "label": "Stationnements PMR dans l'ERP",
        "help_text": mark_safe(
            "Existe-t-il une ou plusieurs places de stationnement adaptées dans l’établissement ou au sein de la parcelle de l'établissement&nbsp;?"
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
        "section": SECTION_STATIONNEMENT,
        "nullable_bool": True,
        "warn_if": False,
    },
    # Cheminement extérieur
    "cheminement_ext_presence": {
        "is_a11y": True,
        "label": "Espace extérieur",
        "help_text": mark_safe(
            "L'établissement dispose-t-il d'un espace extérieur qui lui appartient&nbsp;?"
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": None,
    },
    "cheminement_ext_terrain_accidente": {
        "is_a11y": True,
        "label": "Terrain meuble ou accidenté",
        "help_text": mark_safe(
            "Le revêtement du cheminement extérieur (entre l’entrée de la parcelle et l’entrée de l’établissement) est-il meuble ou accidenté (pavés, gravillons, terre, herbe, ou toute surface non stabilisée)&nbsp;?"
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": True,
    },
    "cheminement_ext_plain_pied": {
        "is_a11y": True,
        "label": "Cheminement de plain-pied",
        "help_text": mark_safe(
            "Le cheminement est-il de plain-pied, c’est-à-dire sans marche ni ressaut supérieur à 2 cm&nbsp;?  Attention plain-pied ne signifie pas plat mais sans rupture brutale de niveau."
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_ascenseur": {
        "is_a11y": True,
        "label": "Ascenseur/élévateur",
        "help_text": mark_safe("Existe-t-il un ascenseur ou un élévateur&nbsp;?"),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_nombre_marches": {
        "is_a11y": True,
        "label": "Nombre de marches",
        "help_text": mark_safe("Indiquer 0 s'il n'y a ni marche ni escalier"),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x > 0,
    },
    "cheminement_ext_reperage_marches": {
        "is_a11y": True,
        "label": "Repérage des marches ou de l’escalier",
        "help_text": mark_safe(
            "L'escalier est-il sécurisé&nbsp;: nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées&nbsp;?"
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
    },
    "cheminement_ext_main_courante": {
        "is_a11y": True,
        "label": "Main courante",
        "help_text": mark_safe("L'escalier est-il équipé d'une main courante&nbsp;?"),
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
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": True,
    },
    # Entrée
    "entree_reperage": {
        "is_a11y": True,
        "label": "Entrée facilement repérable",
        "help_text": mark_safe(
            "Y a-t-il des éléments facilitant le repérage de l'entrée de l’établissement (numéro de rue à proximité, enseigne, etc)&nbsp;?"
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_vitree": {
        "is_a11y": True,
        "label": "Entrée vitrée",
        "help_text": mark_safe("La porte d'entrée est-elle vitrée&nbsp;?"),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": True,
    },
    "entree_vitree_vitrophanie": {
        "is_a11y": True,
        "label": "Vitrophanie",
        "help_text": mark_safe(
            "Si l'entrée est vitrée, y a-t-il des éléments contrastés permettant de visualiser les parties vitrées de l'entrée&nbsp;? "
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
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_ascenseur": {
        "is_a11y": True,
        "label": "Ascenseur/élévateur",
        "help_text": mark_safe("Existe-t-il un ascenseur ou un élévateur&nbsp;?"),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_marches": {
        "is_a11y": True,
        "label": "Marches ou escalier",
        "help_text": mark_safe("Indiquer 0 s'il n'y a ni marche ni escalier"),
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
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_marches_main_courante": {
        "is_a11y": True,
        "label": "Main courante",
        "help_text": mark_safe("L'escalier est-il équipé d'une main courante&nbsp;?"),
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
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_balise_sonore": {
        "is_a11y": True,
        "label": "Balise sonore",
        "help_text": mark_safe(
            "L'entrée est-elle équipée d'une balise sonore facilitant son repérage par une personne aveugle ou malvoyante&nbsp;?"
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_dispositif_appel": {
        "is_a11y": True,
        "label": "Dispositif d'appel",
        "help_text": mark_safe(
            "Existe-t-il un dispositif comme une sonnette pour permettre à quelqu'un ayant besoin de la rampe ou d'une aide humaine de signaler sa présence&nbsp;?"
        ),
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
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_largeur_mini": {
        "is_a11y": True,
        "label": "Largeur minimale en cm",
        "help_text": mark_safe(
            "Si la largeur n'est pas précisément connue, indiquer une valeur minimum. Exemple&nbsp;: la largeur se situe entre 90 et 100 cm&nbsp;; indiquer 90."
        ),
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
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
    },
    "entree_pmr_informations": {
        "is_a11y": True,
        "label": "Infos entrée spécifique PMR",
        "help_text": mark_safe(
            "Préciser ici les modalités d'accès de l'entrée spécifique PMR"
        ),
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
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None
        and x in [PERSONNELS_NON_FORMES, PERSONNELS_AUCUN,],
    },
    "accueil_equipements_malentendants": {
        "is_a11y": True,
        "label": "Équipements sourds/malentendants",
        "help_text": mark_safe(
            "L'accueil est-il équipé de produits ou prestations dédiés aux personnes sourdes ou malentendantes (boucle à induction magnétique, langue des signes française, solution de traduction à distance, etc)"
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": False,
        "warn_if": lambda x, i: x and EQUIPEMENT_MALENTENDANT_AUCUN in x,
    },
    "accueil_cheminement_plain_pied": {
        "is_a11y": True,
        "label": "Cheminement de plain pied",
        "help_text": mark_safe(
            "Le cheminement est-il de plain-pied, c’est-à-dire sans marche ni ressaut supérieur à 2 cm&nbsp;? Attention, plain-pied ne signifie pas plat mais sans rupture brutale de niveau."
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_ascenseur": {
        "is_a11y": True,
        "label": "Ascenseur/élévateur",
        "help_text": mark_safe("Existe-t-il un ascenseur ou un élévateur&nbsp;?"),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_nombre_marches": {
        "is_a11y": True,
        "label": "Nombre de marches",
        "help_text": mark_safe("Indiquer 0 s'il n'y a ni marche ni escalier"),
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
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_cheminement_main_courante": {
        "is_a11y": True,
        "label": "Main courante",
        "help_text": mark_safe("L'escalier est-il équipé d'une main courante&nbsp;?"),
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
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": True,
    },
    "accueil_prestations": {
        "is_a11y": True,
        "label": "Prestations d'accueil adapté supplémentaires",
        "help_text": mark_safe(
            "Prestations spécifiques supplémentaires proposées par l'établissement"
        ),
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
        "section": SECTION_SANITAIRES,
        "nullable_bool": True,
        "warn_if": False,
    },
    "sanitaires_adaptes": {
        "is_a11y": True,
        "label": "Nombre de sanitaires adaptés",
        "help_text": mark_safe("Combien y a-t-il de sanitaires adaptés&nbsp;?"),
        "section": SECTION_SANITAIRES,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x < 1,
    },
    # Labels
    "labels": {
        "is_a11y": True,
        "label": "Marques ou labels",
        "help_text": mark_safe(
            "Si l’établissement est entré dans une démarche volontaire de labellisation, quelle marques ou quels labels a-t-il obtenu&nbsp;?"
        ),
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
        "section": SECTION_LABELS,
        "nullable_bool": False,
        "warn_if": None,
    },
    "labels_autre": {
        "is_a11y": True,
        "label": "Autre label",
        "help_text": mark_safe("Si autre, préciser le nom du label"),
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


def get_section_fields(section_id):
    return [k for (k, v) in FIELDS.items() if v["section"] == section_id]


def get_nullable_bool_fields():
    return [k for (k, v) in FIELDS.items() if v["nullable_bool"] is True]
