from django.apps import apps
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as translate_lazy

from core.lib import text

# This module describes and handles accessibility fields data

UNKNOWN = translate_lazy("Inconnu")
UNKNOWN_OR_NA = translate_lazy("Inconnu ou sans objet")

BOOLEAN_CHOICES = (
    (True, translate_lazy("Oui")),
    (False, translate_lazy("Non")),
)


NULLABLE_BOOLEAN_CHOICES = (
    (True, translate_lazy("Oui")),
    (False, translate_lazy("Non")),
    (None, UNKNOWN),
)

NULLABLE_OR_NA_BOOLEAN_CHOICES = (
    (True, translate_lazy("Oui")),
    (False, translate_lazy("Non")),
    (None, UNKNOWN_OR_NA),
)

DEVERS_AUCUN = "aucun"
DEVERS_LEGER = "léger"
DEVERS_IMPORTANT = "important"
DEVERS_CHOICES = [
    (DEVERS_AUCUN, translate_lazy("Aucun")),
    (DEVERS_LEGER, translate_lazy("Léger")),
    (DEVERS_IMPORTANT, translate_lazy("Important")),
    (None, UNKNOWN),
]

EQUIPEMENT_MALENTENDANT_AUTRES = "autres"
EQUIPEMENT_MALENTENDANT_BIM = "bim"
EQUIPEMENT_MALENTENDANT_BM_PORTATIVE = "bmp"
EQUIPEMENT_MALENTENDANT_LSF = "lsf"
EQUIPEMENT_MALENTENDANT_STS = "sts"
EQUIPEMENT_MALENTENDANT_LPC = "lpc"
EQUIPEMENT_MALENTENDANT_CHOICES = [
    (EQUIPEMENT_MALENTENDANT_BIM, translate_lazy("boucle à induction magnétique fixe")),
    (EQUIPEMENT_MALENTENDANT_BM_PORTATIVE, translate_lazy("boucle à induction magnétique portative")),
    (EQUIPEMENT_MALENTENDANT_LSF, translate_lazy("langue des signes française (LSF)")),
    (EQUIPEMENT_MALENTENDANT_LPC, translate_lazy("langue française parlée complétée (LFPC)")),
    (EQUIPEMENT_MALENTENDANT_STS, translate_lazy("sous-titrage ou transcription simultanée")),
    (EQUIPEMENT_MALENTENDANT_AUTRES, translate_lazy("autres")),
]
EQUIPEMENT_MALENTENDANTS_TO_SHORT_TEXT = {
    (EQUIPEMENT_MALENTENDANT_BIM, translate_lazy("Boucle à induction magnétique")),
    (EQUIPEMENT_MALENTENDANT_BM_PORTATIVE, translate_lazy("Boucle à induction magnétique")),
    (EQUIPEMENT_MALENTENDANT_LSF, translate_lazy("Langue des signes française")),
    (EQUIPEMENT_MALENTENDANT_LPC, translate_lazy("Langue parlée complétée")),
    (EQUIPEMENT_MALENTENDANT_STS, translate_lazy("Sous-titrage et transcription simultanée")),
    (EQUIPEMENT_MALENTENDANT_AUTRES, translate_lazy("Autres")),
}

ACCUEIL_CLASSES_NON_ACCESSIBLE = "aucune"
ACCUEIL_CLASSES_ACCESSIBILITE_PARTIELLE = "partielle"
ACCUEIL_CLASSES_TOUTES_ACCESSIBLES = "toutes"
ACCUEIL_CLASSES_ACCESSIBILITE_CHOICES = [
    (ACCUEIL_CLASSES_NON_ACCESSIBLE, translate_lazy("Aucune salle de classe")),
    (
        ACCUEIL_CLASSES_ACCESSIBILITE_PARTIELLE,
        translate_lazy("Au moins une salle de classe (accessibilité partielle des salles)"),
    ),
    (
        ACCUEIL_CLASSES_TOUTES_ACCESSIBLES,
        translate_lazy("Toutes les salles de classe (accessibilité totale des salles)"),
    ),
]

ACCUEIL_ESPACES_OUVERTS_RESTAURATION = "restauration"
ACCUEIL_ESPACES_OUVERTS_BIBLIOTHEQUE = "bibliotheque"
ACCUEIL_ESPACES_OUVERTS_COUR = "cour"
ACCUEIL_ESPACES_OUVERTS_SANTE = "sante"
ACCUEIL_ESPACES_OUVERTS_CHOICES = [
    (ACCUEIL_ESPACES_OUVERTS_RESTAURATION, translate_lazy("A la cantine ou l’espace restauration")),
    (ACCUEIL_ESPACES_OUVERTS_BIBLIOTHEQUE, translate_lazy("A la bibliothèque ou CDI")),
    (ACCUEIL_ESPACES_OUVERTS_COUR, translate_lazy("Dans la cour")),
    (
        ACCUEIL_ESPACES_OUVERTS_SANTE,
        translate_lazy("Dans les locaux de santé (infirmerie, bureau du médecin scolaire, bureau du psychologue, etc)"),
    ),
]


HANDICAP_AUDITIF = "auditif"
HANDICAP_MENTAL = "mental"
HANDICAP_MOTEUR = "moteur"
HANDICAP_VISUEL = "visuel"
HANDICAP_CHOICES = [
    (HANDICAP_AUDITIF, translate_lazy("Handicap auditif")),
    (HANDICAP_MENTAL, translate_lazy("Handicap mental")),
    (HANDICAP_MOTEUR, translate_lazy("Handicap moteur")),
    (HANDICAP_VISUEL, translate_lazy("Handicap visuel")),
]

DISPOSITIFS_APPEL_BOUTON = "bouton"
DISPOSITIFS_APPEL_INTERPHONE = "interphone"
DISPOSITIFS_APPEL_VISIOPHONE = "visiophone"
DISPOSITIFS_APPEL_CHOICES = [
    (DISPOSITIFS_APPEL_BOUTON, translate_lazy("Bouton d'appel")),
    (DISPOSITIFS_APPEL_INTERPHONE, translate_lazy("Interphone")),
    (DISPOSITIFS_APPEL_VISIOPHONE, translate_lazy("Visiophone")),
]

LABEL_AUTRE = "autre"
LABEL_DPT = "dpt"
LABEL_MOBALIB = "mobalib"
LABEL_TH = "th"
LABEL_HANDIPLAGE = "handiplage"
LABEL_CHOICES = [
    (LABEL_AUTRE, translate_lazy("Autre")),
    (LABEL_DPT, translate_lazy("Destination pour Tous")),
    (LABEL_MOBALIB, translate_lazy("Mobalib")),
    (LABEL_TH, translate_lazy("Tourisme & Handicap")),
    (LABEL_HANDIPLAGE, translate_lazy("Handiplage")),
]

PENTE_LEGERE = "légère"
PENTE_IMPORTANTE = "importante"
PENTE_CHOICES = [
    (PENTE_LEGERE, translate_lazy("Légère")),
    (PENTE_IMPORTANTE, translate_lazy("Importante")),
    (None, UNKNOWN),
]

PENTE_LONGUEUR_COURTE = "courte"
PENTE_LONGUEUR_MOYENNE = "moyenne"
PENTE_LONGUEUR_LONGUE = "longue"
PENTE_LENGTH_CHOICES = [
    (PENTE_LONGUEUR_COURTE, translate_lazy("inférieure à 0,5 mètres")),
    (PENTE_LONGUEUR_MOYENNE, translate_lazy("entre 0,5 et 2 mètres")),
    (PENTE_LONGUEUR_LONGUE, translate_lazy("supérieure 2 mètres")),
    (None, UNKNOWN),
]

PERSONNELS_AUCUN = "aucun"
PERSONNELS_FORMES = "formés"
PERSONNELS_NON_FORMES = "non-formés"
PERSONNELS_CHOICES = [
    (PERSONNELS_AUCUN, translate_lazy("Aucun personnel")),
    (PERSONNELS_FORMES, translate_lazy("Personnels sensibilisés ou formés")),
    (PERSONNELS_NON_FORMES, translate_lazy("Personnels non-formés")),
    (None, UNKNOWN),
]

AUDIODESCRIPTION_AVEC_EQUIPEMENT_PERMANENT = "avec_équipement_permanent"
AUDIODESCRIPTION_AVEC_APP = "avec_app"
AUDIODESCRIPTION_AVEC_EQUIPEMENT_OCCASIONNEL = "avec_équipement_occasionnel"
AUDIODESCRIPTION_SANS_EQUIPEMENT = "sans_équipement"
AUDIODESCRIPTION_CHOICES = [
    (
        AUDIODESCRIPTION_AVEC_EQUIPEMENT_PERMANENT,
        translate_lazy("avec équipement permanent, casques et boîtiers disponibles à l’accueil"),
    ),
    (
        AUDIODESCRIPTION_AVEC_APP,
        translate_lazy("avec équipement permanent nécessitant le téléchargement d'une application sur smartphone"),
    ),
    (AUDIODESCRIPTION_AVEC_EQUIPEMENT_OCCASIONNEL, "avec équipement occasionnel selon la programmation"),
    (
        AUDIODESCRIPTION_SANS_EQUIPEMENT,
        translate_lazy("sans équipement, audiodescription audible par toute la salle (selon la programmation)"),
    ),
]

PORTE_TYPE_MANUELLE = "manuelle"
PORTE_TYPE_AUTOMATIQUE = "automatique"
PORTE_TYPE_CHOICES = [
    (PORTE_TYPE_MANUELLE, translate_lazy("Manuelle")),
    (PORTE_TYPE_AUTOMATIQUE, translate_lazy("Automatique")),
    (None, UNKNOWN_OR_NA),
]

PORTE_MANOEUVRE_BATTANTE = "battante"
PORTE_MANOEUVRE_COULISSANTE = "coulissante"
PORTE_MANOEUVRE_TOURNIQUET = "tourniquet"
PORTE_MANOEUVRE_TAMBOUR = "tambour"
PORTE_MANOEUVRE_CHOICES = [
    (PORTE_MANOEUVRE_BATTANTE, translate_lazy("Porte battante")),
    (PORTE_MANOEUVRE_COULISSANTE, translate_lazy("Porte coulissante")),
    (PORTE_MANOEUVRE_TOURNIQUET, translate_lazy("Tourniquet")),
    (PORTE_MANOEUVRE_TAMBOUR, translate_lazy("Porte tambour")),
    (None, UNKNOWN),
]

RAMPE_AUCUNE = "aucune"
RAMPE_FIXE = "fixe"
RAMPE_AMOVIBLE = "amovible"
RAMPE_CHOICES = [
    (RAMPE_AUCUNE, translate_lazy("Aucune")),
    (RAMPE_FIXE, translate_lazy("Fixe")),
    (RAMPE_AMOVIBLE, translate_lazy("Amovible")),
    (None, UNKNOWN),
]

ESCALIER_MONTANT = "montant"
ESCALIER_DESCENDANT = "descendant"
ESCALIER_SENS = [
    (ESCALIER_MONTANT, translate_lazy("Monter")),
    (ESCALIER_DESCENDANT, translate_lazy("Descendre")),
    (None, UNKNOWN),
]

REGISTRE_INFO_URL = "https://www.ecologie.gouv.fr/politiques-publiques/laccessibilite-etablissements-recevant-du-public-erp#le-registre-public-daccessibilite-6"

PARTNER_LABELS = {
    "TOURISM_AND_LEISURE": translate_lazy("Tourisme & loisirs"),
    "ESTABLISHMENT_MANAGER": translate_lazy("Gestionnaire"),
    "INSTITUTIONAL": translate_lazy("Institutionnel"),
    "ASSOCIATION": translate_lazy("Association"),
    "COMMUNITY": translate_lazy("Collectivité"),
    "GENERAL_INFORMATION_SITE": translate_lazy("Site d'informations"),
    "STUDY_OFFICE": translate_lazy("Bureau d'étude"),
    "SERVICE_DEDICATED_TO_PEOPLE_WITH_DISABILITIES": translate_lazy("Service aux PMR"),
}

PARTNER_ROLES = {"RE_USE": "RE_USE", "COLLECTOR": "COLLECTOR", "FUNDERS": "FUNDERS"}

PARTENAIRES = {
    "FRANCE_RELANCE": {
        "avatar": "france_relance.png",
        "logo": "img/partenaires/france_relance.png",
        "name": "France Relance",
        "template": "editorial/partenaires/france_relance.html",
        "url": "https://www.economie.gouv.fr/plan-de-relance",
        "labels": [PARTNER_LABELS["INSTITUTIONAL"]],
        "roles": [PARTNER_ROLES["FUNDERS"]],
    },
    "DESTINATION_POUR_TOUS": {
        "avatar": "destination_pour_tous.png",
        "logo": "img/partenaires/destination_pour_tous.png",
        "name": "Destination pour tous",
        "template": "editorial/partenaires/destination_pour_tous.html",
        "url": "https://www.entreprises.gouv.fr/",
        "labels": [PARTNER_LABELS["INSTITUTIONAL"]],
        "roles": [PARTNER_ROLES["COLLECTOR"]],
    },
    "THE_FORK": {
        "logo": "img/partenaires/the_fork.png",
        "name": "The Fork",
        "template": "editorial/partenaires/the_fork.html",
        "url": "https://www.thefork.fr/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"]],
    },
    "MICHELIN": {
        "logo": "img/partenaires/michelin.png",
        "name": "Michelin",
        "template": "editorial/partenaires/michelin.html",
        "url": "https://guide.michelin.com/fr/fr",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "MAC_DONALD_S": {
        "logo": "img/partenaires/mcdo.png",
        "name": "MC Donald's",
        "template": "editorial/partenaires/mac_donald_s.html",
        "url": "https://www.mcdonalds.fr/",
        "labels": [PARTNER_LABELS["ESTABLISHMENT_MANAGER"]],
        "roles": [PARTNER_ROLES["RE_USE"]],
    },
    "PATHE": {
        "logo": "img/partenaires/pathe.png",
        "name": "Pathé",
        "template": "editorial/partenaires/pathe.html",
        "url": "https://www.pathe.fr/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "GROUPE_BERTRAND": {
        "logo": "img/partenaires/groupe_bertrand.png",
        "name": "Groupe Bertrand",
        "template": "editorial/partenaires/groupe_bertrand.html",
        "url": "https://www.groupe-bertrand.com/",
        "labels": [PARTNER_LABELS["ESTABLISHMENT_MANAGER"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "EXPEDIA_GROUP": {
        "logo": "img/partenaires/expedia_group.png",
        "name": "Expedia Group",
        "template": "editorial/partenaires/expedia_group.html",
        "url": "https://expediagroup.com/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "LE_PETIT_FUTE": {
        "logo": "img/partenaires/le_petit_fute.png",
        "name": "Le Petit Futé",
        "template": "editorial/partenaires/le_petit_fute.html",
        "url": "https://www.petitfute.com/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"]],
    },
    "LE_PETIT_PAUME": {
        "logo": "img/partenaires/le_petit_paume.png",
        "name": "Le Petit Paumé",
        "template": "editorial/partenaires/le_petit_paume.html",
        "url": "https://www.petitpaume.com/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"]],
    },
    "NOUVELLE_AQUITAINE": {
        "logo": "img/partenaires/nouvelle_aquitaine.png",
        "name": "Le CRT Nouvelle-Aquitaine",
        "template": "editorial/partenaires/nouvelle_aquitaine.html",
        "url": "https://www.crt-nouvelle-aquitaine.com/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "ADN_TOURISME": {
        "logo": "img/partenaires/adn_tourisme.png",
        "name": "ADN Tourisme",
        "template": "editorial/partenaires/adn_tourisme.html",
        "url": "https://www.adn-tourisme.fr/",
        "labels": [PARTNER_LABELS["INSTITUTIONAL"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "AGGLOMERATION_LORIENT": {
        "logo": "img/partenaires/agglomeration_lorient.png",
        "name": "Agglomération de Lorient",
        "template": "editorial/partenaires/agglomeration_lorient.html",
        "url": "https://www.lorient-agglo.bzh/",
        "labels": [PARTNER_LABELS["COMMUNITY"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "OFFICE_DE_TOURISME_DIEPPE_NORMANDIE": {
        "logo": "img/partenaires/office_de_tourisme_dieppe_normandie.png",
        "name": "Office de Tourisme Dieppe-Normandie",
        "template": "editorial/partenaires/office_de_tourisme_dieppe_normandie.html",
        "url": "https://www.dieppetourisme.com/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "OFFICE_DE_TOURISME_DE_AVRE_LUCE_NOYE": {
        "logo": "img/partenaires/office_de_tourisme_de_avre_luce_noye.png",
        "name": "Office de Tourisme de Avre Luce Noye",
        "template": "editorial/partenaires/office_de_tourisme_de_avre_luce_noye.html",
        "url": "https://www.tourisme-avrelucenoye.fr/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "PARIS_JE_T_AIME": {
        "logo": "img/partenaires/paris_je_t_aime.png",
        "name": "Paris Je t'aime - Office de Tourisme",
        "template": "editorial/partenaires/paris_je_t_aime.html",
        "url": "https://parisjetaime.com/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "FEDERATION_DES_OFFICES_DE_TOURISME_DE_BRETAGNE": {
        "logo": "img/partenaires/federation_des_offices_de_tourisme_de_bretagne.png",
        "name": "Fédération des Offices de tourisme de Bretagne",
        "template": "editorial/partenaires/federation_des_offices_de_tourisme_de_bretagne.html",
        "url": "https://otb.bzh/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "MUSIC_IN_PARIS": {
        "logo": "img/partenaires/music_in_paris.png",
        "name": "Music in Paris",
        "template": "editorial/partenaires/music_in_paris.html",
        "url": "https://musicinparis.fr/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "LE_FOODING": {
        "logo": "img/partenaires/le_fooding.png",
        "name": "Le Fooding",
        "template": "editorial/partenaires/le_fooding.html",
        "url": "https://lefooding.com/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "PASS_CULTURE": {
        "logo": "img/partenaires/pass_culture.png",
        "name": "Pass Culture",
        "template": "editorial/partenaires/pass_culture.html",
        "url": "https://pass.culture.fr/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "DIJOP": {
        "logo": "img/partenaires/dijop.png",
        "name": "Pass Culture",
        "template": "editorial/partenaires/dijop.html",
        "url": "https://www.info.gouv.fr/organisation/delegation-jeux-olympiques-paralympiques-paris-2024#:~:text=La%20D%C3%A9l%C3%A9gation%20interminist%C3%A9rielle%20aux%20Jeux,les%20actions%20des%20diff%C3%A9rents%20minist%C3%A8res",
        "labels": [PARTNER_LABELS["INSTITUTIONAL"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "UMIH": {
        "logo": "img/partenaires/umih.png",
        "name": "L'Union des Métiers et des Industries de l'Hôtellerie",
        "template": "editorial/partenaires/umih.html",
        "url": "https://www.umih.fr/",
        "labels": [PARTNER_LABELS["ESTABLISHMENT_MANAGER"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "JE_VEUX_AIDER": {
        "logo": "img/partenaires/je_veux_aider.png",
        "name": "Je Veux Aider",
        "template": "editorial/partenaires/je_veux_aider.html",
        "url": "https://www.jeveuxaider.gouv.fr/",
        "labels": [PARTNER_LABELS["ASSOCIATION"]],
        "roles": [PARTNER_ROLES["COLLECTOR"]],
    },
    "VILLE_DE_PARIS": {
        "logo": "img/partenaires/ville_de_paris.png",
        "name": "Ville de Paris",
        "template": "editorial/partenaires/ville_de_paris.html",
        "url": "https://www.paris.fr/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "TOURISME_HANDICAPS": {
        "logo": "img/partenaires/tourisme_handicaps.png",
        "name": "Association tourisme & Handicaps",
        "template": "editorial/partenaires/tourisme_handicaps.html",
        "url": "https://tourisme-handicaps.org/",
        "labels": [PARTNER_LABELS["ASSOCIATION"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "LUCIE": {
        "avatar": "lucie_avatar.png",
        "logo": "img/partenaires/lucie.png",
        "name": "RSE Lucie",
        "short_description": translate_lazy("La RSE Positive"),
        "template": "editorial/partenaires/lucie.html",
        "url": "https://agence-lucie.com/",
        "labels": [PARTNER_LABELS["INSTITUTIONAL"]],
        "roles": [PARTNER_ROLES["RE_USE"]],
    },
    "MOBALIB": {
        "avatar": "mobalib_avatar.jpg",
        "logo": "img/partenaires/mobalib.png",
        "name": "Mobalib",
        "short_description": translate_lazy("Mobalib, l'expert du handicap"),
        "template": "editorial/partenaires/mobalib.html",
        "url": "https://www.mobalib.com/",
        "labels": [PARTNER_LABELS["SERVICE_DEDICATED_TO_PEOPLE_WITH_DISABILITIES"]],
        "roles": [PARTNER_ROLES["RE_USE"]],
    },
    "WEGOTO": {
        "avatar": "wegoto_avatar.png",
        "logo": "img/partenaires/wegoto.png",
        "name": "Wegoto",
        "short_description": translate_lazy("Expert en données d'accessibilité"),
        "template": "editorial/partenaires/wegoto.html",
        "url": "https://www.wegoto.eu/",
        "labels": [PARTNER_LABELS["SERVICE_DEDICATED_TO_PEOPLE_WITH_DISABILITIES"]],
        "roles": [PARTNER_ROLES["RE_USE"]],
    },
    "ACCESMETRIE": {
        "avatar": "accesmetrie_avatar.png",
        "logo": "img/partenaires/accesmetrie.png",
        "name": "AccèsMétrie",
        "short_description": translate_lazy("Bureau d'étude accessibilité"),
        "template": "editorial/partenaires/accesmetrie.html",
        "url": "http://www.accesmetrie.com",
        "labels": [PARTNER_LABELS["STUDY_OFFICE"]],
        "roles": [PARTNER_ROLES["COLLECTOR"]],
    },
    "ONECOMPAGNON": {
        "avatar": "onecompagnon_avatar.jpg",
        "logo": "img/partenaires/one_campagnon.png",
        "name": "One Compagnon",
        "short_description": translate_lazy("L'assistant accessible à tous"),
        "template": "editorial/partenaires/onecompagnon.html",
        "url": "https://www.onecompagnon.com",
        "labels": [PARTNER_LABELS["SERVICE_DEDICATED_TO_PEOPLE_WITH_DISABILITIES"]],
        "roles": [PARTNER_ROLES["RE_USE"]],
    },
    "SORTIRAPARIS": {
        "avatar": "sortir-a-paris_avatar.png",
        "logo": "img/partenaires/sortir_a_paris.png",
        "name": "Sortir À Paris",
        "short_description": translate_lazy("Premier média d'actualité Sorties en France"),
        "template": "editorial/partenaires/sortiraparis.html",
        "url": "https://www.sortiraparis.com",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"]],
    },
    "NESTENN": {
        "avatar": "nestenn_avatar.png",
        "logo": "img/partenaires/nestenn.png",
        "name": "Nestenn",
        "short_description": translate_lazy("Groupe d'agences immobilières"),
        "template": "editorial/partenaires/nestenn.html",
        "url": "https://nestenn.com/groupe-immobilier-nestenn",
        "labels": [PARTNER_LABELS["ESTABLISHMENT_MANAGER"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "ANDRE_DE_CABO": {
        "avatar": "andre_cabo_avatar.jpg",
        "logo": "img/partenaires/andre_de_cabo.png",
        "name": "André de CABO",
        "short_description": translate_lazy("Notre vocation est de vous conseiller et de vous accompagner"),
        "template": "editorial/partenaires/andre_de_cabo.html",
        "url": "https://andredecabo.fr/",
        "labels": [PARTNER_LABELS["STUDY_OFFICE"]],
        "roles": [PARTNER_ROLES["COLLECTOR"]],
    },
    "CFPSAA": {
        "avatar": "cfpsaa_avatar.png",
        "logo": "img/partenaires/cfpsaa.png",
        "name": "Confédération Française pour la Promotion Sociale des Aveugles et Amblyopes",
        "short_description": translate_lazy(
            "Confédération regroupant une vingtaine des principales associations de déficients visuels"
        ),
        "template": "editorial/partenaires/cfpsaa.html",
        "url": "https://www.cfpsaa.fr/",
        "weight": 100,
        "labels": [PARTNER_LABELS["ASSOCIATION"]],
        "roles": [PARTNER_ROLES["COLLECTOR"]],
    },
    "AVH": {
        "avatar": "avh_avatar.png",
        "logo": "img/partenaires/avh.png",
        "name": "Association Valentin Haüy",
        "short_description": translate_lazy("association d'aide aux personnes déficientes visuelles"),
        "template": "editorial/partenaires/avh.html",
        "url": "https://www.avh.asso.fr/",
        "weight": 100,
        "labels": [PARTNER_LABELS["ASSOCIATION"]],
        "roles": [PARTNER_ROLES["COLLECTOR"]],
    },
    "LAPOSTE": {
        "avatar": "laposte.png",
        "logo": "img/partenaires/laposte.png",
        "name": "La Poste",
        "short_description": translate_lazy("Service universel postal"),
        "template": "editorial/partenaires/laposte.html",
        "url": "https://laposte.fr/",
        "weight": 100,
        "labels": [PARTNER_LABELS["ESTABLISHMENT_MANAGER"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "ALLOCINE": {
        "avatar": "allocine.png",
        "logo": "img/partenaires/allocine.png",
        "name": "AlloCiné",
        "short_description": translate_lazy("Le site de référence des actualités cinéma, films et séries..."),
        "template": "editorial/partenaires/allocine.html",
        "url": "https://www.allocine.fr",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "CRT_NORMANDIE": {
        "avatar": "crt_normandie.png",
        "logo": "img/partenaires/crt_normandie.png",
        "name": "Comité Régional du Tourisme de Normandie",
        "short_description": translate_lazy("Base de données touristique normande"),
        "template": "editorial/partenaires/crt_normandie.html",
        "url": "https://pronormandietourisme.fr/outils/la-base-de-donnees/",
        "labels": [PARTNER_LABELS["TOURISM_AND_LEISURE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
    "SOLOCAL": {
        "avatar": "solocal.png",
        "logo": "img/partenaires/solocal.png",
        "name": "Solocal",
        "short_description": translate_lazy("1er acteur français du marketing digital"),
        "template": "editorial/partenaires/solocal.html",
        "url": "https://www.solocal.com",
        "labels": [PARTNER_LABELS["GENERAL_INFORMATION_SITE"]],
        "roles": [PARTNER_ROLES["RE_USE"]],
    },
    "SERVICE_PUBLIC": {
        "avatar": "sp.png",
        "logo": "img/partenaires/sp.png",
        "name": "Service-Public.fr",
        "short_description": translate_lazy("L'annuaire de l'administration française"),
        "template": "editorial/partenaires/sp.html",
        "url": "https://lannuaire.service-public.fr/",
        "labels": [PARTNER_LABELS["GENERAL_INFORMATION_SITE"]],
        "roles": [PARTNER_ROLES["RE_USE"], PARTNER_ROLES["COLLECTOR"]],
    },
}

SECTION_A_PROPOS = "a_propos"
SECTION_TRANSPORT = "transport"
SECTION_CHEMINEMENT_EXT = "cheminement_ext"
SECTION_ENTREE = "entree"
SECTION_ACCUEIL = "accueil"
SECTION_REGISTRE = "registre"
SECTION_CONFORMITE = "conformite"
SECTION_ACTIVITE = "activite"
SECTION_COMMENTAIRE = "commentaire"
SECTIONS = {
    SECTION_TRANSPORT: {
        "icon": "bus",
        "label": translate_lazy("Accès"),
        "description": translate_lazy("à proximité"),
        "edit_route": "contrib_transport",
    },
    SECTION_CHEMINEMENT_EXT: {
        "icon": "road",
        "label": translate_lazy("Extérieur entre le trottoir et l’entrée principale du bâtiment"),
        "description": translate_lazy("depuis la voirie jusqu'à l'entrée"),
        "edit_route": "contrib_exterieur",
    },
    SECTION_ENTREE: {
        "icon": "entrance",
        "label": translate_lazy("Entrée"),
        "description": translate_lazy("de l'établissement"),
        "edit_route": "contrib_entree",
    },
    SECTION_ACCUEIL: {
        "icon": "users",
        # Translators: This is for reception, not for home
        "label": translate_lazy("Accueil - Réception"),
        "description": translate_lazy("et prestations"),
        "edit_route": "contrib_accueil",
    },
    SECTION_REGISTRE: {
        "icon": "registre",
        "label": translate_lazy("Registre"),
        "description": translate_lazy("d'accessibilité de l'établissement"),
        "edit_route": None,
    },
    SECTION_CONFORMITE: {
        "icon": "conformite",
        "label": translate_lazy("Conformité"),
        "description": translate_lazy("à la réglementation"),
        "edit_route": None,
    },
    SECTION_COMMENTAIRE: {
        "icon": "info-circled",
        "label": translate_lazy("Commentaire"),
        "description": translate_lazy("et informations complémentaires"),
        "edit_route": "contrib_commentaire",
    },
}


FIELDS = {
    # NOTE root(true|false) determines whether a field is a nested field or a root one. A root one can be made of 0 to N sub non root fields.
    #        In the UI, the sub fields are visible only if the root field has given value.
    #        Default is False if not provided.
    # NOTE conditional(None|hosting|school|floor) determines whether a field is always display or if it is display only under certain conditions. Like if field has
    #        sense only for a category of activities.
    #        Default is None if not provided.
    # NOTE free_text(true|false) determines whether a field is a free text/a user input or not. If yes, it's intented to be cleaned from profanities and
    #        translated on front end side.
    #        Default is False if not provided.
    # Transport
    "transport_station_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Proximité d'un arrêt de transport en commun"),
        "help_text": mark_safe(
            translate_lazy(
                "Existe-t-il un arrêt de transport en commun à moins de 200 mètres de l'établissement&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy("Arrêt de transport en commun à moins de 200 mètres de l'établissement"),
        "help_text_ui_v2": translate_lazy("Transport en commun à proximité"),
        "help_text_ui_neg": translate_lazy(
            "Pas d'arrêt de transport en commun à moins de 200 mètres de l'établissement"
        ),
        "help_text_ui_neg_v2": translate_lazy("Pas de transport en commun à proximité"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/arret-transport-en-commun.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_TRANSPORT,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": True,
    },
    "transport_information": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Informations complémentaires"),
        "help_text": mark_safe(
            translate_lazy(
                "Préciser ici les informations supplémentaires sur ces transports (type de transport, ligne, nom de l'arrêt, etc) et éventuellement des informations jugées importantes sur le chemin qui relie le point d'arrêt à l'établissement."
            )
        ),
        "help_text_ui": translate_lazy("Informations sur l'accessibilité par les transports en commun"),
        "help_text_ui_neg": translate_lazy("Informations sur l'accessibilité par les transports en commun"),
        "choices": None,
        "section": SECTION_TRANSPORT,
        "nullable_bool": False,
        "warn_if": None,
        "example": "Ligne n4",
        "free_text": True,
        "root": False,
    },
    # Stationnement
    "stationnement_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Stationnement privé dans l'établissement"),
        "help_text": mark_safe(
            translate_lazy(
                "Existe-t-il une ou plusieurs places de stationnement dans l'établissement ou au sein de la parcelle de l'établissement&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Des places de stationnement sont disponibles au sein de la parcelle de l'établissement"
        ),
        "help_text_ui_v2": translate_lazy("Places de parking au sein de l'établissement"),
        "help_text_ui_neg": translate_lazy(
            "Pas de place de stationnement disponible au sein de la parcelle de l'établissement"
        ),
        "help_text_ui_neg_v2": translate_lazy("Pas de places de parking au sein de l'établissement"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/panneau-stationnement-prive.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_TRANSPORT,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": True,
    },
    "stationnement_pmr": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Stationnements adaptés dans l'établissement"),
        "should_display_label": False,
        "help_text": mark_safe(
            translate_lazy(
                "Existe-t-il une ou plusieurs places de stationnement adaptées dans l'établissement ou au sein de la parcelle de l'établissement&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Des places de stationnement adaptées sont disponibles au sein de la parcelle de l'établissement"
        ),
        "help_text_ui_v2": translate_lazy(
            "Places de parking au sein de l'établissement comprenant des places adaptées et réservées"
        ),
        "help_text_ui_neg": translate_lazy(
            "Pas de place de stationnement disponible adaptée au sein de la parcelle de l'établissement"
        ),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/panneau-stationnement-adaptes.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_TRANSPORT,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": False,
    },
    "stationnement_ext_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Stationnement à proximité de l'établissement"),
        "help_text": mark_safe(
            translate_lazy(
                "Existe-t-il une ou plusieurs places de stationnement en voirie ou en parking à moins de 200 mètres de l'établissement&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Des places de stationnement sont disponibles à moins de 200 mètres de l'établissement"
        ),
        "help_text_ui_v2": translate_lazy("Places de parking à proximité"),
        "help_text_ui_neg": translate_lazy(
            "Pas de place de stationnement disponible à moins de 200 mètres de l'établissement"
        ),
        "help_text_ui_neg_v2": translate_lazy("Pas de places de parking à proximité"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/place-stationnement-a-proximite.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_TRANSPORT,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": True,
    },
    "stationnement_ext_pmr": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Stationnements adaptés à proximité de l'établissement"),
        "should_display_label": False,
        "help_text": mark_safe(
            translate_lazy(
                "Existe-t-il une ou plusieurs places de stationnement adaptées en voirie ou en parking à moins de 200 mètres de l'établissement&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Des places de stationnement adaptées sont disponibles à moins de 200 mètres de l'établissement"
        ),
        "help_text_ui_v2": translate_lazy("Places de parking à proximité comprenant des places adaptées et réservées"),
        "help_text_ui_neg": translate_lazy(
            "Pas de place de stationnement disponible adaptée à moins de 200 mètres de l'établissement"
        ),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/place-stationnement-adapte.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_TRANSPORT,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": False,
    },
    # Cheminement extérieur
    "cheminement_ext_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Extérieur entre le trottoir et l’entrée principale du bâtiment"),
        "help_text": mark_safe(
            translate_lazy(
                "Y-a-t-il un chemin extérieur entre le trottoir et l'entrée principale du bâtiment (exemple&nbsp;: une cour)&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy("L'accès à l'entrée depuis la voirie se fait par un chemin extérieur"),
        "help_text_ui_v2": translate_lazy(
            "Présence d'un chemin sur la parcelle de l'établissement qui mène à l'entrée"
        ),
        "help_text_ui_neg": translate_lazy(
            "Pas de chemin extérieur entre le trottoir et l'entrée principale du bâtiment"
        ),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/chemin-exterieur-entre-trottoire-et-entree-principale.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": True,
        "free_text": False,
        "root": True,
    },
    "cheminement_ext_terrain_stable": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Revêtement extérieur"),
        "should_display_label": False,
        "help_text": mark_safe(
            translate_lazy(
                "Le revêtement du chemin extérieur (entre le trottoir et l'entrée de l'établissement) est-il stable (sol roulable, absence de pavés ou de gravillons, pas de terre ni d'herbe, etc.)&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Le revêtement est stable (absence de pavés, gravillons, terre, herbe, sable, ou toute surface non stabilisée)"
        ),
        "help_text_ui_v2": translate_lazy("Revêtement adapté au passage d’un fauteuil roulant"),
        "help_text_ui_neg": translate_lazy(
            "Le revêtement n'est pas stable (pavés, gravillons, terre, herbe, sable, ou toute surface non stabilisée)"
        ),
        "help_text_ui_neg_v2": translate_lazy("Revêtement non adapté au passage d'un fauteuil roulant"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/chemin-stable.png"),
            ("/static/img/contrib/chemin-instable.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": False,
    },
    "cheminement_ext_plain_pied": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Chemin extérieur de plain-pied"),
        "should_display_label": False,
        "help_text": mark_safe(
            translate_lazy(
                "Le chemin est-il de plain-pied, c'est-à-dire sans marche ni ressaut supérieur à 2 centimètres&nbsp;? Attention plain-pied ne signifie pas plat mais sans rupture brutale de niveau."
            )
        ),
        "help_text_ui": translate_lazy(
            "L'accès à cet espace se fait de plain-pied, c'est à dire sans rupture brutale de niveau"
        ),
        "help_text_ui_v2": translate_lazy("Chemin extérieur de plain pied"),
        "help_text_ui_neg": translate_lazy(
            "L'accès à cet espace n'est pas de plain-pied et présente une rupture brutale de niveau"
        ),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/chemin-plain-pied.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": False,
    },
    "cheminement_ext_ascenseur": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Ascenseur/élévateur"),
        "should_display_label": False,
        "help_text": mark_safe(translate_lazy("Existe-t-il un ascenseur ou un élévateur&nbsp;?")),
        "help_text_ui": translate_lazy("Présence d'un ascenseur ou un élévateur"),
        "help_text_ui_v2": translate_lazy("Ascenseur ou élévateur"),
        "help_text_ui_neg": translate_lazy("Pas d'ascenseur ou d'élévateur"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/ascenseur-elevateur.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
        "description": translate_lazy("Existe-t-il un ascenseur ou un élévateur&nbsp;?"),
        "free_text": False,
        "root": False,
    },
    "cheminement_ext_nombre_marches": {
        "type": "number",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Nombre de marches"),
        "help_text": mark_safe(translate_lazy("Indiquer 0 s'il n'y a ni marche ni escalier")),
        "help_text_ui": translate_lazy("Nombre de marches de l'escalier"),
        "help_text_ui_neg": translate_lazy("Aucune marche d'escalier"),
        "section": SECTION_CHEMINEMENT_EXT,
        "choices": None,
        "unit": "marche",
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x > 0,
        "description": translate_lazy("Combien y'a t'il de marches&nbsp;?"),
        "free_text": False,
        "root": False,
    },
    "cheminement_ext_sens_marches": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Sens de circulation de l'escalier"),
        "help_text": mark_safe(translate_lazy("Faut-il monter ou descendre  les marches pour atteindre l'entrée ?")),
        "help_text_ui": translate_lazy("Sens de circulation des marches ou de l'escalier"),
        "help_text_ui_neg": translate_lazy("Sens de circulation des marches ou de l'escalier"),
        "choices": ESCALIER_SENS,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": None,
        "free_text": False,
    },
    "cheminement_ext_reperage_marches": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Repérage des marches"),
        "help_text": mark_safe(
            translate_lazy(
                "L'escalier est-il sécurisé&nbsp;: nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Présence de nez de marche contrastés, d'une bande d'éveil à la vigilance en haut de l'escalier et/ou de première et dernière contremarches contrastées"
        ),
        "help_text_ui_neg": translate_lazy(
            "Pas de nez de marche contrasté, de bande d'éveil à la vigilance en haut de l'escalier ni de première et dernière contremarches contrastées"
        ),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/reperage-marches.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
    },
    "cheminement_ext_main_courante": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Main courante"),
        "should_display_label": False,
        "help_text": mark_safe(translate_lazy("L'escalier est-il équipé d'une ou plusieurs main-courantes&nbsp;?")),
        "help_text_ui": translate_lazy("L'escalier est équipé d'une ou plusieurs main-courantes"),
        "help_text_ui_v2": translate_lazy("Équipé d'une ou plusieurs mains courantes"),
        "help_text_ui_neg": translate_lazy("L'escalier n'est pas équipé de main-courante"),
        "help_text_ui_neg_v2": translate_lazy("Non équipé de main courante."),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/escalier-avec-main-courantes.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
    },
    "cheminement_ext_rampe": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Rampe"),
        "help_text": mark_safe(
            translate_lazy("S'il existe une rampe ayant une pente douce, est-elle fixe ou amovible&nbsp;?")
        ),
        "help_text_ui": translate_lazy("Présence d'une rampe fixe ou amovible"),
        "help_text_ui_v2": translate_lazy("Présence d'une rampe"),
        "help_text_ui_neg": translate_lazy("Pas de rampe fixe ou amovible"),
        "help_text_ui_neg_v2": translate_lazy("Pas de rampe"),
        "choices": RAMPE_CHOICES,
        "choices_images": (
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/rampe-fixe.png"),
            ("/static/img/contrib/rampe-amovible.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": RAMPE_AUCUNE,
        "free_text": False,
    },
    "cheminement_ext_pente_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Pente"),
        "help_text": mark_safe(translate_lazy("Le chemin est-il en pente&nbsp;?")),
        "help_text_ui": translate_lazy("Le chemin est en pente"),
        "help_text_ui_neg": translate_lazy("Le chemin n'est pas en pente"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": True,
        "free_text": False,
    },
    "cheminement_ext_pente_degre_difficulte": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Degré de difficulté de la pente"),
        "should_display_label": False,
        "help_text": mark_safe(translate_lazy("Quel est son degré de difficulté&nbsp;?")),
        "help_text_ui": translate_lazy("Difficulté de la pente"),
        "help_text_ui_neg": translate_lazy("Difficulté de la pente"),
        "choices": PENTE_CHOICES,
        "choices_images": (
            ("/static/img/contrib/chemin-pente-legere.png"),
            ("/static/img/contrib/chemin-pente-importante.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None and x in [PENTE_LEGERE, PENTE_IMPORTANTE],
        "free_text": False,
    },
    "cheminement_ext_pente_longueur": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Longueur de la pente"),
        "should_display_label": False,
        "help_text": mark_safe(translate_lazy("Longueur de la pente")),
        "choices": PENTE_LENGTH_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None and x in [PENTE_LONGUEUR_MOYENNE, PENTE_LONGUEUR_LONGUE],
        "free_text": False,
    },
    "cheminement_ext_devers": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Dévers"),
        "help_text": mark_safe(
            translate_lazy(
                "Existe t-il un dévers sur le chemin ? Quel est son degré de difficulté ? Un dévers est une inclinaison transversale du chemin."
            )
        ),
        "help_text_ui": translate_lazy("Dévers ou inclinaison transversale du chemin"),
        "help_text_ui_neg": translate_lazy("Pas de dévers ou d'inclinaison transversale du chemin"),
        "help_text_ui_neg_v2": translate_lazy("Pas de dévers"),
        "choices": DEVERS_CHOICES,
        "choices_images": (
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/devers-leger.png"),
            ("/static/img/contrib/devers-important.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None and x in [DEVERS_LEGER, DEVERS_IMPORTANT],
        "free_text": False,
    },
    "cheminement_ext_bande_guidage": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Bande de guidage"),
        "help_text": mark_safe(
            translate_lazy(
                "Présence d'une bande de guidage au sol facilitant le déplacement d'une personne aveugle ou malvoyante"
            )
        ),
        "help_text_ui": translate_lazy(
            "Présence d'une bande de guidage au sol facilitant le déplacement d'une personne aveugle ou malvoyante"
        ),
        "help_text_ui_v2": translate_lazy("Bande de guidage"),
        "help_text_ui_neg": translate_lazy(
            "Pas de bande de guidage au sol facilitant le déplacement d'une personne aveugle ou malvoyante"
        ),
        "help_text_ui_neg_v2": translate_lazy("Pas de bande de guidage"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/bande-de-guidage.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
    },
    "cheminement_ext_retrecissement": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Rétrécissement du chemin"),
        "help_text": mark_safe(
            translate_lazy(
                "Existe-t-il un ou plusieurs rétrécissements (inférieur à 90 centimètres) du chemin emprunté par le public pour atteindre l'entrée&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Un ou plusieurs rétrécissements inférieurs à 90 centimètres du chemin pour atteindre la zone d'accueil"
        ),
        "help_text_ui_v2": translate_lazy("Présence de rétrécissement inférieur à 90 cm sur le chemin"),
        "help_text_ui_neg": translate_lazy(
            "Pas de rétrécissement inférieur à 90 centimètres du chemin pour atteindre la zone d'accueil"
        ),
        "help_text_ui_neg_v2": translate_lazy("Largeur minimale de 90 cm sur tout le chemin"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_CHEMINEMENT_EXT,
        "nullable_bool": True,
        "warn_if": True,
        "free_text": False,
    },
    # Entrée
    "entree_reperage": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("L’entrée de l’établissement"),
        "help_text": mark_safe(
            translate_lazy(
                "Y a-t-il des éléments facilitant le repérage de l'entrée de l'établissement (numéro de rue à proximité, enseigne, végétaux, éléments architecturaux contrastés, etc)&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy("L'entrée de l'établissement est facilement repérable"),
        "help_text_ui_v2": translate_lazy("Entrée bien visible"),
        "help_text_ui_neg": translate_lazy(
            "Pas d'éléments facilitant le repérage de l'entrée de l'établissement (numéro de rue à proximité, enseigne, végétaux, éléments architecturaux contrastés, etc)"
        ),
        "help_text_ui_neg_v2": translate_lazy("L'entrée n'est pas bien visible"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "choices_images": (
            ("/static/img/contrib/entree-etablissement-reperage.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": True,
    },
    "entree_porte_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Porte d'entrée"),
        "help_text": mark_safe(translate_lazy("Y a-t-il une porte à l'entrée de l'établissement&nbsp;?")),
        "help_text_ui": translate_lazy("Présence d'une porte à l'entrée de l'établissement"),
        "help_text_ui_neg": translate_lazy("Pas de porte à l'entrée de l'établissement"),
        "help_text_ui_neg_v2": translate_lazy("Pas de porte"),
        "choices": BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": None,
        "required": True,
        "free_text": False,
        "root": True,
    },
    "entree_porte_manoeuvre": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Manoeuvre de la porte"),
        "help_text": mark_safe(translate_lazy("Comment s'ouvre la porte&nbsp;?")),
        "help_text_ui": translate_lazy("Mode d'ouverture de la porte"),
        "help_text_ui_neg": translate_lazy("Mode d'ouverture de la porte"),
        "choices": PORTE_MANOEUVRE_CHOICES,
        "choices_images": (
            ("/static/img/contrib/porte-battante.png"),
            ("/static/img/contrib/porte-coulissante.png"),
            ("/static/img/contrib/tourniquet.png"),
            ("/static/img/contrib/porte-tambour.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": None,
        "free_text": False,
    },
    "entree_porte_type": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Type de porte"),
        "should_display_label": False,
        "help_text": mark_safe(translate_lazy("Quel est le type de la porte&nbsp;?")),
        "help_text_ui": translate_lazy("Type de porte"),
        "help_text_ui_neg": translate_lazy("Type de porte"),
        "choices": PORTE_TYPE_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": None,
        "free_text": False,
    },
    "entree_vitree": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Entrée vitrée"),
        "should_display_label": False,
        "help_text": mark_safe(translate_lazy("La porte d'entrée est-elle vitrée&nbsp;?")),
        "help_text_ui": translate_lazy("La porte d'entrée est vitrée"),
        "help_text_ui_v2": translate_lazy("Porte vitrée"),
        "help_text_ui_neg": translate_lazy("La porte d'entrée n'est pas vitrée"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": True,
        "free_text": False,
    },
    "entree_vitree_vitrophanie": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Repérage de la vitre"),
        "should_display_label": False,
        "help_text": mark_safe(
            translate_lazy(
                "Y a-t-il des éléments contrastés (autocollants, éléments de menuiserie ou autres) permettant de repérer la porte vitrée&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Des éléments contrastés permettent de visualiser les parties vitrées de l'entrée"
        ),
        "help_text_ui_v2": translate_lazy("Avec éléments contrastés sur la partie vitrée"),
        "help_text_ui_neg": translate_lazy(
            "Pas d'éléments contrastés permettant de visualiser les parties vitrées de l'entrée"
        ),
        "help_text_ui_neg_v2": translate_lazy("Sans éléments contrastés sur la partie vitrée"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
    },
    "entree_plain_pied": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Entrée de plain-pied"),
        "help_text": mark_safe(
            translate_lazy(
                "L'entrée est-elle de plain-pied, c'est-à-dire sans marche ni ressaut supérieur à 2 centimètres&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy("L'entrée se fait de plain-pied, c'est à dire sans rupture brutale de niveau"),
        "help_text_ui_v2": translate_lazy("Entrée de plain pied"),
        "help_text_ui_neg": translate_lazy(
            "L'entrée n'est pas de plain-pied et présente une rupture brutale de niveau"
        ),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": True,
    },
    "entree_ascenseur": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Ascenseur/élévateur"),
        "should_display_label": False,
        "help_text": mark_safe(translate_lazy("Existe-t-il un ascenseur ou un élévateur&nbsp;?")),
        "help_text_ui": translate_lazy("Présence d'un ascenseur ou d'un élévateur"),
        "help_text_ui_neg": translate_lazy("Pas d'ascenseur ou d'élévateur"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/ascenseur-elevateur.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
    },
    "entree_marches": {
        "type": "number",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Nombre de marches"),
        "help_text": mark_safe(translate_lazy("Indiquer 0 s'il n'y a ni marche ni escalier")),
        "help_text_ui": translate_lazy("Nombre de marches de l'escalier"),
        "help_text_ui_neg": translate_lazy("Pas de marches d'escalier"),
        "choices": None,
        "unit": "marche",
        "section": SECTION_ENTREE,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x > 0,
        "free_text": False,
    },
    "entree_marches_sens": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Sens de circulation de l'escalier"),
        "help_text": mark_safe(translate_lazy("Faut-il monter ou descendre  les marches pour atteindre l'entrée ?")),
        "help_text_ui": translate_lazy("Sens de circulation des marches ou de l'escalier"),
        "help_text_ui_neg": translate_lazy("Sens de circulation des marches ou de l'escalier"),
        "choices": ESCALIER_SENS,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": None,
        "free_text": False,
    },
    "entree_marches_reperage": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Repérage des marches"),
        "help_text": mark_safe(
            translate_lazy(
                "L'escalier est-il sécurisé&nbsp;: nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Présence de nez de marche contrastés, d'une bande d'éveil à la vigilance en haut de l'escalier et/ou de première et dernière contremarches contrastées"
        ),
        "help_text_ui_neg": translate_lazy(
            "Pas de nez de marche contrasté, de bande d'éveil à la vigilance en haut de l'escalier ni de première et dernière contremarches contrastées"
        ),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/reperage-marches.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
    },
    "entree_marches_main_courante": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Main courante"),
        "should_display_label": False,
        "help_text": mark_safe(translate_lazy("L'escalier est-il équipé d'une ou plusieurs main-courantes&nbsp;?")),
        "help_text_ui": translate_lazy("L'escalier est équipé d'une ou plusieurs main-courantes"),
        "help_text_ui_neg": translate_lazy("L'escalier n'est pas équipé de main-courante"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/escalier-avec-main-courantes.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
    },
    "entree_marches_rampe": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Rampe"),
        "help_text": mark_safe(
            translate_lazy("S'il existe une rampe ayant une pente douce, est-elle fixe ou amovible&nbsp;?")
        ),
        "help_text_ui": translate_lazy("Présence d'une rampe fixe ou amovible"),
        "help_text_ui_v2": translate_lazy("Présence d'une rampe"),
        "help_text_ui_neg": translate_lazy("Pas de rampe fixe ou amovible"),
        "help_text_ui_neg_v2": translate_lazy("Pas de rampe"),
        "choices": RAMPE_CHOICES,
        "choices_images": (
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/rampe-fixe.png"),
            ("/static/img/contrib/rampe-amovible.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is False or x == RAMPE_AUCUNE,
        "free_text": False,
    },
    "entree_dispositif_appel": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Type de dispositif d'appel à l'entrée"),
        "help_text": mark_safe(
            translate_lazy(
                "Existe-t-il un dispositif pour permettre à quelqu'un signaler sa présence à l'entrée&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy("Présence d'un dispositif comme une sonnette pour signaler sa présence"),
        "help_text_ui_v2": translate_lazy("Dispositif d'appel à l'entrée"),
        "help_text_ui_neg": translate_lazy("Pas de dispositif comme une sonnette pour signaler sa présence"),
        "help_text_ui_neg_v2": translate_lazy("Pas de dispositif d'appel"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": True,
    },
    "entree_dispositif_appel_type": {
        "type": "array",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Dispositif d’appel à l’entrée"),
        "help_text": mark_safe(translate_lazy("De quel type est le dispositif d’appel ?")),
        "help_text_ui": translate_lazy("Dispositifs d'appels présents"),
        "help_text_ui_neg": translate_lazy("Dispositifs d'appels présents"),
        "choices": DISPOSITIFS_APPEL_CHOICES,
        "choices_images": (
            ("/static/img/contrib/bouton-d-appel.png"),
            ("/static/img/contrib/interphone.png"),
            ("/static/img/contrib/visiophone.png"),
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
    },
    "entree_balise_sonore": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Balise sonore à l'entrée"),
        "help_text": mark_safe(
            translate_lazy(
                "L'entrée est-elle équipée d'une balise sonore facilitant son repérage par une personne aveugle ou malvoyante&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Présence d'une balise sonore facilitant son repérage par une personne aveugle ou malvoyante"
        ),
        "help_text_ui_v2": translate_lazy("Balise sonore"),
        "help_text_ui_neg": translate_lazy(
            "Pas de balise sonore facilitant son repérage par une personne aveugle ou malvoyante"
        ),
        "help_text_ui_neg_v2": translate_lazy("Pas de balise sonore"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/balise-sonore.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": True,
    },
    "entree_aide_humaine": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Aide humaine"),
        "help_text": mark_safe(translate_lazy("Présence ou possibilité d'une aide humaine au déplacement")),
        "help_text_ui": translate_lazy("Possibilité d'une aide humaine au déplacement"),
        "help_text_ui_v2": translate_lazy("Aide humaine possible"),
        "help_text_ui_neg": translate_lazy("Pas de possibilité d'aide humaine au déplacement"),
        "help_text_ui_neg_v2": translate_lazy("Pas de possibilité d'aide humaine"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": True,
    },
    "entree_largeur_mini": {
        "type": "number",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Largeur de la porte ou de l'entrée"),
        "help_text": mark_safe(
            translate_lazy(
                "Si la largeur n'est pas précisément connue, indiquer une valeur minimum. Exemple&nbsp;: la largeur se situe entre 90 et 100 centimètres&nbsp;; indiquer 90."
            )
        ),
        "help_text_ui": translate_lazy("Largeur minimale de la porte d'entrée"),
        "help_text_ui_v2": translate_lazy("Largeur d'au moins 80 cm"),
        "help_text_ui_neg": translate_lazy("Largeur minimale de la porte d'entrée"),
        "help_text_ui_neg_v2": translate_lazy("Largeur inférieure à 80 cm"),
        "choices": None,
        "unit": "centimètre",
        "section": SECTION_ENTREE,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x < 80,
        "free_text": False,
        "root": True,
    },
    "entree_pmr": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Entrée dédiée aux personnes en situation de handicap"),
        "help_text": mark_safe(
            translate_lazy(
                "Existe-t-il une entrée secondaire spécifique dédiée aux personnes à mobilité réduite&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Présence d'une entrée secondaire spécifique dédiée aux personnes à mobilité réduite"
        ),
        "help_text_ui_v2": translate_lazy("Présence d'une entrée dédiée aux personnes en situation de handicap"),
        "help_text_ui_neg": translate_lazy(
            "Pas d'entrée secondaire spécifique dédiée aux personnes à mobilité réduite"
        ),
        "help_text_ui_neg_v2": translate_lazy("Pas d’entrée dédiée aux personnes en situation de handicap"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ENTREE,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": True,
    },
    "entree_pmr_informations": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy(
            "Informations complémentaires concernant l'entrée dédiée aux personnes en situation de handicap"
        ),
        "help_text": mark_safe(translate_lazy("Précisions sur les modalités d'accès de l'entrée spécifique PMR")),
        "help_text_ui": translate_lazy("Précisions sur les modalités d'accès de l'entrée spécifique PMR"),
        "help_text_ui_neg": translate_lazy("Précisions sur les modalités d'accès de l'entrée spécifique PMR"),
        "choices": None,
        "section": SECTION_ENTREE,
        "nullable_bool": False,
        "warn_if": None,
        "free_text": True,
        "example": "Entrée fléchée",
    },
    # Accueil
    "accueil_visibilite": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Visibilité de la zone d'accueil"),
        "help_text": mark_safe(
            translate_lazy(
                "La zone d'accueil (guichet d'accueil, caisse, secrétariat, etc) est-elle visible depuis l'entrée du bâtiment ? (Cette information est utile aux personnes aveugles ou malvoyantes qui peuvent être directement prises en charge par le personnel d'accueil si l'accueil se trouve à proximité direct de l'entrée)"
            )
        ),
        "help_text_ui": translate_lazy(
            "La zone d'accueil (guichet d'accueil, caisse, secrétariat, etc) est visible depuis l'entrée du bâtiment"
        ),
        "help_text_ui_v2": translate_lazy("Accueil à proximité directe de l'entrée"),
        "help_text_ui_neg": translate_lazy(
            "La zone d'accueil (guichet d'accueil, caisse, secrétariat, etc) n'est pas visible depuis l'entrée du bâtiment"
        ),
        "help_text_ui_neg_v2": translate_lazy("Accueil éloigné de l'entrée"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": True,
    },
    "accueil_cheminement_plain_pied": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Chemin entre l'entrée principale du bâtiment et l'accueil de l'établissement"),
        "help_text": mark_safe(
            translate_lazy(
                "Une fois l'entrée du bâtiment passée, le chemin jusqu'à l'accueil de l'établissement est t-il de plain-pied, c'est-à-dire sans marche ni ressaut supérieur à 2 centimètres&nbsp;? (attention, plain-pied ne signifie pas plat mais sans rupture brutale de niveau)"
            )
        ),
        "help_text_ui": translate_lazy(
            "L'accès à cet espace se fait de plain-pied, c'est à dire sans rupture brutale de niveau"
        ),
        "help_text_ui_v2": translate_lazy("Chemin vers l'accueil de plain pied"),
        "help_text_ui_neg": translate_lazy(
            "L'accès à cet espace n'est pas de plain-pied et présente une rupture brutale de niveau"
        ),
        "choices": (
            (True, translate_lazy("Oui, sans rupture de niveau brutale")),
            (False, translate_lazy("Non")),
            (None, UNKNOWN),
        ),
        "choices_images": (
            ("/static/img/contrib/chemin-sans-rupture-brutale-de-niveau.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": True,
    },
    "accueil_cheminement_ascenseur": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Ascenseur/élévateur"),
        "should_display_label": False,
        "help_text": mark_safe(translate_lazy("Existe-t-il un ascenseur ou un élévateur&nbsp;?")),
        "help_text_ui": translate_lazy("Présence d'un ascenseur ou un élévateur"),
        "help_text_ui_neg": translate_lazy("Pas d'ascenseur ou d'élévateur"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/ascenseur-elevateur.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
    },
    "accueil_cheminement_nombre_marches": {
        "type": "number",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Nombre de marches"),
        "help_text": mark_safe(translate_lazy("Indiquer 0 s'il n'y a ni marche ni escalier")),
        "help_text_ui": translate_lazy("Nombre de marches de l'escalier"),
        "help_text_ui_neg": translate_lazy("Pas de marches d'escalier"),
        "choices": None,
        "unit": "marche",
        "section": SECTION_ACCUEIL,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x > 0,
        "free_text": False,
    },
    "accueil_cheminement_sens_marches": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Sens de circulation de l'escalier"),
        "help_text": mark_safe(translate_lazy("Faut-il monter ou descendre  les marches pour atteindre l'entrée ?")),
        "help_text_ui": translate_lazy("Sens de circulation des marches ou de l'escalier"),
        "help_text_ui_neg": translate_lazy("Sens de circulation des marches ou de l'escalier"),
        "choices": ESCALIER_SENS,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": None,
        "free_text": False,
    },
    "accueil_cheminement_reperage_marches": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Repérage des marches ou de l'escalier"),
        "help_text": mark_safe(
            translate_lazy(
                "L'escalier est-il sécurisé&nbsp;: nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches contrastées&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Nez de marche contrastés, bande d'éveil à la vigilance en haut de l'escalier et/ou première et dernière contremarches contrastées"
        ),
        "help_text_ui_neg": translate_lazy(
            "Pas de nez de marche contrasté, de bande d'éveil à la vigilance en haut de l'escalier ni de première et dernière contremarches contrastées"
        ),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/reperage-marches.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
    },
    "accueil_cheminement_main_courante": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Main courante"),
        "should_display_label": False,
        "help_text": mark_safe(translate_lazy("L'escalier est-il équipé d'une ou plusieurs main-courantes&nbsp;?")),
        "help_text_ui": translate_lazy("L'escalier est équipé d'une ou plusieurs main-courantes"),
        "help_text_ui_neg": translate_lazy("L'escalier n'est pas équipé de main-courante"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/escalier-avec-main-courantes.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
    },
    "accueil_cheminement_rampe": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Rampe"),
        "help_text": mark_safe(
            translate_lazy("S'il existe une rampe ayant une pente douce, est-elle fixe ou amovible&nbsp;?")
        ),
        "help_text_ui": translate_lazy("Présence d'une rampe fixe ou amovible"),
        "help_text_ui_v2": translate_lazy("Présence d'une rampe"),
        "help_text_ui_neg": translate_lazy("Pas de rampe fixe ou amovible"),
        "choices": RAMPE_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
    },
    "accueil_retrecissement": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Rétrécissement du chemin"),
        "should_display_label": False,
        "help_text": mark_safe(
            translate_lazy(
                "Existe-t-il un ou plusieurs rétrécissements (inférieur à 90 centimètres) du chemin emprunté par le public pour atteindre la zone d'accueil&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Présence d'un ou plusieurs rétrécissements inférieurs à 90 centimètres du chemin pour atteindre la zone d'accueil"
        ),
        "help_text_ui_v2": translate_lazy("Présence de rétrécissement inférieur à 90 cm pour atteindre l'accueil"),
        "help_text_ui_neg": translate_lazy(
            "Pas de rétrécissement inférieur à 90 centimètres du chemin pour atteindre la zone d'accueil"
        ),
        "help_text_ui_neg_v2": translate_lazy("Largeur minimale de 90 cm sur toute la circulation menant à l'accueil"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": True,
        "free_text": False,
        "root": True,
    },
    "accueil_chambre_nombre_accessibles": {
        "type": "number",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Nombre de chambres accessibles à une personne en fauteuil roulant"),
        "help_text": mark_safe(
            translate_lazy(
                "Nombre de chambres accessibles à une personne en fauteuil roulant : espace et aménagement suffisant pour permettre à une personne en fauteuil de circuler dans la chambre, atteindre le lit et tourner (espace de rotation d’au moins 150 cm de diamètre)"
            )
        ),
        "help_text_ui": translate_lazy("Nombre de chambres accessibles à une personne en fauteuil roulant"),
        "help_text_ui_neg": translate_lazy("Aucune chambre accessible à une personne en fauteuil roulant"),
        "help_text_ui_neg_v2": translate_lazy("Pas de chambre accessible"),
        "choices": None,
        "unit": "chambre",
        "section": SECTION_ACCUEIL,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is not None and x < 80,
        "free_text": False,
        "root": True,
        "conditional": "hosting",
    },
    "accueil_chambre_douche_plain_pied": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Douche accessible"),
        "help_text": mark_safe(
            translate_lazy(
                "La douche est-elle à l'italienne ou équipée d'un bac extra plat (hauteur inférieure à 2 cm)&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy("La douche est à l'italienne ou équipée d'un bac extra plat"),
        "help_text_ui_v2": translate_lazy("Douche à l'italienne (bac plat)"),
        "help_text_ui_neg": translate_lazy("La douche n'est pas à l'italienne ni équipée d'un bac extra plat"),
        "help_text_ui_neg_v2": translate_lazy("Douche classique, avec ressaut ou marche"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/douche-accessible.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": True,
        "free_text": False,
        "root": False,
        "conditional": "hosting",
    },
    "accueil_chambre_douche_siege": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Siège de douche"),
        "help_text": mark_safe(
            translate_lazy(
                "La douche est-elle équipée d'un siège de douche normé et d'une largeur minimum de 40 cm&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy("La douche est équipée d'un siège de douche"),
        "help_text_ui_v2": translate_lazy("Avec siège de douche"),
        "help_text_ui_neg": translate_lazy("La douche n'est pas équipée d'un siège de douche"),
        "help_text_ui_neg_v2": translate_lazy("Sans siège de douche"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/siege-de-douche.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": True,
        "free_text": False,
        "root": False,
        "conditional": "hosting",
    },
    "accueil_chambre_douche_barre_appui": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Douche sécurisée"),
        "help_text": mark_safe(
            translate_lazy(
                "La douche est-elle équipée d'une barre d'appui horizontale permettant le transfert depuis un fauteuil vers le siège de douche&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy("La douche est équipée d'une barre d'appui horizontale"),
        "help_text_ui_v2": translate_lazy("Avec Barre d'appui"),
        "help_text_ui_neg": translate_lazy("La douche n'est pas équipée d'une barre d'appui horizontale"),
        "help_text_ui_neg_v2": translate_lazy("Sans barre d'appui"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/douche-securisee.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": True,
        "free_text": False,
        "root": False,
        "conditional": "hosting",
    },
    "accueil_chambre_sanitaires_barre_appui": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Toilettes sécurisées"),
        "help_text": mark_safe(translate_lazy("Les toilettes sont-elles équipées d'une barre d'appui horizontal ?")),
        "help_text_ui": translate_lazy("Les toilettes sont équipées d'une barre d'appui horizontale"),
        "help_text_ui_v2": translate_lazy("Avec Barre d'appui"),
        "help_text_ui_neg": translate_lazy("Le toilette n'est pas équipé d'une barre d'appui horizontale"),
        "help_text_ui_neg_v2": translate_lazy("Sans barre d'appui"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/toilette-securisee.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": True,
        "free_text": False,
        "root": False,
        "conditional": "hosting",
    },
    "accueil_chambre_sanitaires_espace_usage": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Toilettes accessibles"),
        "help_text": mark_safe(
            translate_lazy(
                "Les toilettes disposent-elles d'un espace d'usage (80 cm x 130 cm) à côté de la cuvette&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy("Le toilette dispose d'un espace d'usage à côté de la cuvette"),
        "help_text_ui_v2": translate_lazy("Avec espace d'usage"),
        "help_text_ui_neg": translate_lazy("Le toilette ne dispose pas d'un espace d'usage à côté de la cuvette"),
        "help_text_ui_neg_v2": translate_lazy("Sans espace d'usage"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/toilette-accessible.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": True,
        "free_text": False,
        "root": False,
        "conditional": "hosting",
    },
    "accueil_chambre_numero_visible": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Visibilité des numéros de chambres"),
        "help_text": mark_safe(
            translate_lazy(
                "Les numéros de chambres sont-ils bien repérables et en relief (très contrastés, positionnés à hauteur des yeux, soit 160 cm, au milieu de la porte ou au-dessus de la poignée, et relief d’au moins 2 cm d’épaisseur) ?"
            )
        ),
        "help_text_ui": translate_lazy("Les numéros de chambres sont repérables et en relief"),
        "help_text_ui_v2": translate_lazy("Numéros de chambre en relief"),
        "help_text_ui_neg": translate_lazy("Les numéros de chambres ne sont pas repérables et en relief"),
        "help_text_ui_neg_v2": translate_lazy("Numéros de chambre sans relief"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/numero-de-chambre.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": True,
        "free_text": False,
        "root": True,
        "conditional": "hosting",
    },
    "accueil_chambre_equipement_alerte": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Equipement d'alerte adapté"),
        "help_text": mark_safe(
            translate_lazy(
                "L'établissement dispose-t-il d'un ou plusieurs équipements d'alerte par flash lumineux ou vibration&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "L'établissement dispose d'un ou plusieurs équipements d'alerte par flash lumineux ou vibration"
        ),
        "help_text_ui_v2": translate_lazy("Equipement d'alerte par flash lumineux ou vibration"),
        "help_text_ui_neg": translate_lazy(
            "L'établissement ne dispose pas d'équipement d'alerte par flash lumineux ou vibration"
        ),
        "help_text_ui_neg_v2": translate_lazy("Pas d'équipement d'alerte par flash lumineux ou vibration"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/chambre-alarme.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": True,
        "free_text": False,
        "root": True,
        "conditional": "hosting",
    },
    "accueil_chambre_accompagnement": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Accompagnement spécifique"),
        "help_text": mark_safe(
            translate_lazy(
                "Est-il proposé un accompagnement personnalisé pour présenter la chambre à un client en situation de handicap, notamment aveugle ou malvoyant&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Il est proposé un accompagnement personnalisé pour présenter la chambre à un client en situation de handicap, notamment aveugle ou malvoyant"
        ),
        "help_text_ui_v2": translate_lazy("Accompagnement personnalisé pour présenter la chambre"),
        "help_text_ui_neg": translate_lazy(
            "Aucun accompagnement personnalisé pour présenter la chambre à un client en situation de handicap n'est proposé"
        ),
        "help_text_ui_neg_v2": translate_lazy(
            "Pas de possibilité d'accompagnement personnalisé pour présenter la chambre"
        ),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": True,
        "free_text": False,
        "root": True,
        "conditional": "hosting",
    },
    "accueil_personnels": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Personnel d'accueil"),
        "help_text": mark_safe(
            translate_lazy(
                "En cas de présence du personnel, est-il formé ou sensibilisé à l'accueil des personnes handicapées&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy("Personnel à l'accueil des personnes handicapées"),
        "help_text_ui_neg": translate_lazy("Aucun personnel à l'accueil des personnes handicapées"),
        "choices": PERSONNELS_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None
        and x
        in [
            PERSONNELS_NON_FORMES,
            PERSONNELS_AUCUN,
        ],
        "free_text": False,
        "root": True,
    },
    "accueil_audiodescription_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Audiodescription"),
        "help_text": mark_safe(translate_lazy("L'établissement propose-t-il de l’audiodescription&nbsp?")),
        "help_text_ui": translate_lazy("L'établissement propose l'audiodescription"),
        "help_text_ui_v2": translate_lazy("Audiodescription"),
        "help_text_ui_neg": translate_lazy("L'établissement ne propose pas l’audiodescription"),
        "help_text_ui_neg_v2": translate_lazy("Pas d'audiodescription"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": True,
    },
    "accueil_audiodescription": {
        "type": "array",
        "nullable": False,
        "is_a11y": True,
        "label": translate_lazy("Type d'équipements pour l'audiodescription"),
        "should_display_label": False,
        "help_text": translate_lazy("L'établissement propose-t-il de l’audiodescription ?"),
        "help_text_ui": translate_lazy("Équipements disponibles"),
        "help_text_ui_neg": translate_lazy("Équipements disponibles"),
        "choices": AUDIODESCRIPTION_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None and len(x) == 0,
        "free_text": False,
    },
    "accueil_equipements_malentendants_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Présence d’équipements d’aide à l’audition et à la compréhension"),
        "help_text": mark_safe(
            translate_lazy(
                "L’accueil est-il équipé de produits dédiés à faciliter la communication entre le personnel et les personnes ayant des difficultés à entendre, à comprendre ou à parler ?"
            )
        ),
        "help_text_ui": translate_lazy(
            "Présence de produits ou prestations dédiés aux personnes sourdes ou malentendantes"
        ),
        "help_text_ui_v2": translate_lazy("Présence d'équipement d'aide à l'audition et à la compréhension"),
        "help_text_ui_neg": translate_lazy(
            "Pas de produits ou prestations dédiés aux personnes sourdes ou malentendantes"
        ),
        "help_text_ui_neg_v2": translate_lazy("Pas d'équipement d'aide à l'audition"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/appareil-facilitant-communication.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": True,
    },
    "accueil_equipements_malentendants": {
        "type": "array",
        "nullable": False,
        "is_a11y": True,
        "label": translate_lazy("Liste des équipements d'aide à l'audition et à la communication"),
        "help_text": mark_safe(
            translate_lazy(
                "Sélectionnez les équipements ou prestations disponibles à l'accueil de l'établissement&nbsp;:"
            )
        ),
        "help_text_ui": translate_lazy("Équipements ou prestations disponibles"),
        "help_text_ui_neg": translate_lazy("Équipements ou prestations disponibles"),
        "choices": EQUIPEMENT_MALENTENDANT_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": lambda x, i: x is not None and len(x) == 0,
        "free_text": False,
    },
    "accueil_ascenceur_etage": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Ascenceur desservant le ou les étages"),
        "help_text": mark_safe(
            translate_lazy(
                "Y a-t-il un ascenseur ou un élévateur qui dessert le ou les étages ouverts au public de l’établissement&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy("Ascenceur desservant le ou les étages"),
        "help_text_ui_neg": translate_lazy("Pas d'ascenseur desservant le ou les étages"),
        "choices": NULLABLE_OR_NA_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/ascenseur-elevateur.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "conditional": "floor",
    },
    "accueil_ascenceur_accessibilite": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Accessibilité de l’ascenseur"),
        "help_text": mark_safe(
            translate_lazy(
                "Cet ascenseur ou cet élévateur est-il suffisamment large pour être utilisé par une personne en fauteuil roulant, c’est-à-dire au moins 1m de large x 1,25m de long et 0,80 m de passage utile de la porte&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy("L’ascenseur est accessible"),
        "help_text_ui_neg": translate_lazy("L’ascenseur n’est pas accessible"),
        "choices": NULLABLE_OR_NA_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/ascenseur-elevateur.png"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "conditional": "floor",
    },
    "accueil_classes_accessibilite": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Accessibilité des salles de classes"),
        "help_text": mark_safe(translate_lazy("Une personne en fauteuil roulant peut accéder à :")),
        "help_text_ui": translate_lazy("Accessibilité des salles de classes"),
        "help_text_ui_neg": translate_lazy("Accessibilité des salles de classes"),
        "choices": ACCUEIL_CLASSES_ACCESSIBILITE_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "conditional": "school",
    },
    "accueil_espaces_ouverts": {
        "type": "array",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Accessibilité des différents espaces ouverts aux élèves ou étudiants"),
        "help_text": mark_safe(translate_lazy("Une personne en fauteuil roulant peut se rendre :")),
        "help_text_ui": translate_lazy("Accessibilité des différents espaces ouverts aux élèves ou étudiants"),
        "help_text_ui_neg": translate_lazy("Accessibilité des différents espaces ouverts aux élèves ou étudiants"),
        "choices": ACCUEIL_ESPACES_OUVERTS_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "conditional": "school",
    },
    # Sanitaires
    "sanitaires_presence": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Toilettes"),
        "help_text": mark_safe(translate_lazy("Y a-t-il des toilettes mises à disposition du public&nbsp;?")),
        "help_text_ui": translate_lazy("Des sanitaires sont mis à disposition dans l'établissement"),
        "help_text_ui_neg": translate_lazy("Pas de sanitaires mis à disposition dans l'établissement"),
        "help_text_ui_neg_v2": translate_lazy("Pas de toilettes"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
        "root": True,
    },
    "sanitaires_adaptes": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Toilettes adaptées"),
        "should_display_label": False,
        "help_text": translate_lazy("Y a-t-il des toilettes adaptées PMR (personne à mobilité réduite)"),
        "help_text_ui": translate_lazy("Des sanitaires adaptés sont mis à disposition dans l'établissement"),
        "help_text_ui_neg": translate_lazy("Aucun sanitaire adapté mis à disposition dans l'établissement"),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "choices_images": (
            ("/static/img/contrib/toilette-adaptees.jpg"),
            ("/static/img/contrib/no.png"),
            ("/static/img/contrib/unknown.png"),
        ),
        "section": SECTION_ACCUEIL,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
    },
    # Labels
    "labels": {
        "type": "array",
        "nullable": False,
        "is_a11y": True,
        "label": translate_lazy("Marques ou labels"),
        "help_text": mark_safe(
            translate_lazy(
                "Si l'établissement est entré dans une démarche volontaire de labellisation liée au handicap, quelle marque ou quel label a-t-il obtenu(e)&nbsp;?"
            )
        ),
        "help_text_ui": translate_lazy("Marque(s) ou label(s) obtenus par l'établissement"),
        "help_text_ui_neg": translate_lazy("Marque(s) ou label(s) obtenus par l'établissement"),
        "choices": LABEL_CHOICES,
        "section": SECTION_COMMENTAIRE,
        "nullable_bool": False,
        "warn_if": None,
        "free_text": False,
        "root": True,
    },
    "labels_familles_handicap": {
        "type": "array",
        "nullable": False,
        "is_a11y": True,
        "label": translate_lazy("Famille(s) de handicap concernées(s)"),
        "help_text": mark_safe(
            translate_lazy("Quelle(s) famille(s) de handicap sont couvertes par ces marques et labels&nbsp;?")
        ),
        "help_text_ui": translate_lazy("Famille(s) de handicap couverte(s) par ces marques ou labels"),
        "help_text_ui_neg": translate_lazy("Famille(s) de handicap couverte(s) par ces marques ou labels"),
        "choices": HANDICAP_CHOICES,
        "section": SECTION_COMMENTAIRE,
        "nullable_bool": False,
        "warn_if": None,
        "free_text": False,
    },
    "labels_autre": {
        "type": "string",
        "nullable": True,
        "is_a11y": True,
        "label": translate_lazy("Autre label"),
        "help_text": mark_safe(translate_lazy("Si autre, préciser le nom du label")),
        "help_text_ui": translate_lazy("Autre marque ou label obtenus"),
        "help_text_ui_neg": translate_lazy("Autre marque ou label obtenus"),
        "choices": None,
        "section": SECTION_COMMENTAIRE,
        "nullable_bool": False,
        "warn_if": None,
        "free_text": True,
        "example": "HandiLabel",
    },
    # Commentaire
    "commentaire": {
        "type": "string",
        "nullable": True,
        "is_a11y": False,
        "label": mark_safe(translate_lazy("Autres remarques")),
        "help_text": mark_safe(
            translate_lazy(
                "Ajoutez ici toute information supplémentaire concernant l'accessibilité du bâtiment ou des prestations spécifiques proposées."
            )
        ),
        "help_text_ui": translate_lazy(
            "Informations supplémentaires concernant l'accessibilité du bâtiment ou des prestations spécifiques proposées"
        ),
        "help_text_ui_neg": translate_lazy(
            "Informations supplémentaires concernant l'accessibilité du bâtiment ou des prestations spécifiques proposées"
        ),
        "choices": None,
        "section": SECTION_COMMENTAIRE,
        "nullable_bool": False,
        "warn_if": None,
        "free_text": True,
        "example": "Propose des places gratuites",
        "root": True,
    },
    # Registre
    "registre_url": {
        "type": "string",
        "nullable": True,
        "is_a11y": False,
        "label": translate_lazy("Registre"),
        "help_text": mark_safe(
            translate_lazy(
                'Si l\'établissement en dispose, adresse internet (URL) à laquelle le <a href="{registre_url}" target="_blank">registre d\'accessibilité</a> de l\'établissement est consultable.'.format(
                    registre_url=REGISTRE_INFO_URL
                )
            )
        ),
        "help_text_ui": translate_lazy("Adresse internet à laquelle le registre est consultable"),
        "help_text_ui_neg": translate_lazy("Adresse internet à laquelle le registre est consultable"),
        "section": SECTION_REGISTRE,
        "nullable_bool": False,
        "warn_if": lambda x, i: x is None,
        "free_text": False,
        "example": f"{REGISTRE_INFO_URL}",
    },
    # Conformité
    "conformite": {
        "type": "boolean",
        "nullable": True,
        "is_a11y": False,
        "label": translate_lazy("Conformité"),
        "help_text": mark_safe(
            translate_lazy("L'établissement est-il déclaré conforme ? (réservé à l'administration)")
        ),
        "help_text_ui": translate_lazy("L'établissement a été déclaré conforme à la réglementation"),
        "help_text_ui_v2": translate_lazy("Déclaré conforme à la réglementation"),
        "help_text_ui_neg": translate_lazy(
            "l'établissement n'a pas été déclaré conforme à la réglementation auprès de l'administration"
        ),
        "choices": NULLABLE_BOOLEAN_CHOICES,
        "section": SECTION_CONFORMITE,
        "nullable_bool": True,
        "warn_if": False,
        "free_text": False,
    },
    # Activité
    "activite": {
        "type": "string",
        "nullable": False,
        "is_a11y": False,
        "label": translate_lazy("Activité"),
        "help_text": mark_safe(translate_lazy("Domaine d'activité de l'ERP")),
        "help_text_ui": translate_lazy("Domaine d'activité de l'ERP"),
        "help_text_ui_neg": translate_lazy("Domaine d'activité de l'ERP"),
        "app_model": ("erp", "Activite"),
        "attribute": "nom",
        "nullable_bool": True,
        "section": SECTION_ACTIVITE,
        "free_text": False,
    },
}
# Fix me : write additional documentation


def get_api_fieldsets():
    # {"id_section": {
    #   "label": translate_lazy("Nom de la section"),
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
    #     {"label": translate_lazy("Nom du champ"),
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
    #   "description": translate_lazy("Description de la section"),
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
        return apps.get_model(*field.get("app_model")).objects.all().values_list(field.get("attribute"), flat=True)
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


def get_labels(include_conditional: list[str] = None):
    default_labels = dict((k, v.get("label")) for (k, v) in FIELDS.items() if not v.get("conditional"))
    if not include_conditional:
        return default_labels
    return default_labels | dict(
        (k, v.get("label")) for (k, v) in FIELDS.items() if v.get("conditional", "") in include_conditional
    )


def get_label(field, default=""):
    try:
        return FIELDS[field].get("label", default)
    except KeyError:
        return default


def get_help_texts(include_conditional: list[str] = None):
    default_help_texts = dict((k, v.get("help_text")) for (k, v) in FIELDS.items() if not v.get("conditional"))
    if not include_conditional:
        return default_help_texts
    return default_help_texts | dict(
        (k, v.get("help_text")) for (k, v) in FIELDS.items() if v.get("conditional", "") in include_conditional
    )


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


def get_nullable(field) -> bool:
    return FIELDS[field].get("nullable")


def get_nullable_bool_fields() -> list[str]:
    return [k for (k, v) in FIELDS.items() if v["nullable_bool"] is True]


def get_required_fields() -> list[str]:
    return [k for (k, v) in FIELDS.items() if "required" in v and v["required"] is True]


def get_conditional_fields() -> list[str]:
    return [k for (k, v) in FIELDS.items() if v.get("conditional", False)]


def get_section_fields(section_id) -> list[str]:
    return [k for (k, v) in FIELDS.items() if v["section"] == section_id]


def get_free_text_fields() -> list[str]:
    return [k for (k, v) in FIELDS.items() if v.get("free_text", False) is True]


def get_type(field):
    return FIELDS[field].get("type")
