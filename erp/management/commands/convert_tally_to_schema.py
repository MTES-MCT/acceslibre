import csv
import json

from django.conf import settings
from django.core.management.base import BaseCommand

from erp.imports.mapper.base import BaseMapper
from erp.models import Erp
from erp.provider.geocoder import geocode

with_activity = True
with_comment = False
with_siret = False

# 4 kinds of templates : basic (default), hosting, culture, ath
hosting = False
culture = False
ath = False

if settings.TEST:
    hosting = False
    culture = True
    ath = False

to_ignore_headers = [
    "Submission ID",
    "Respondent ID",
    "Submitted at",
    "Votre établissement :",
]


mapping = {
    "Est-ce qu’il y a au moins une place handicapé dans votre parking ?": {
        "Oui, nous avons une place handicapé": [
            ("stationnement_presence", True),
            ("stationnement_pmr", True),
        ],
        "Non, nous n'avons pas de place handicapé": [
            ("stationnement_pmr", False),
        ],
        "Je ne suis pas sûr": [],
    },
    "Votre établissement :": {
        "Oui, au moins une marche": [("entree_plain_pied", False)],
        "Non, c'est de plain-pied": [("entree_plain_pied", True)],
        "Je ne suis pas sûr": [],
    },
    "Ce chemin n'est pas praticable car :": {
        "Problème de pente": [
            ("cheminement_ext_presence", True),
            ("cheminement_ext_pente_presence", True),
            ("cheminement_ext_pente_degre_difficulte", "importante"),
        ],
        "Problème de marche": [
            ("cheminement_ext_presence", True),
            ("cheminement_ext_plain_pied", False),
            ("cheminement_ext_ascenseur", False),
            ("cheminement_ext_rampe", "aucune"),
        ],
        "Terrain non roulant": [("cheminement_ext_presence", True), ("cheminement_ext_terrain_stable", False)],
        "Autre": [],
        "Je ne suis pas sûr": [],
    },
    "Est-ce qu’il y a au moins une place handicapé dans les environs ?": {
        "Oui, il y a une place de parking handicapé pas loin": [
            ("stationnement_ext_presence", True),
            ("stationnement_ext_pmr", True),
        ],
        # DEPRECATED ANSWER, just here for back compatibility but not used in new tally templates.
        "Non, pas de place handicapé pas loin": [
            ("stationnement_ext_presence", True),
            ("stationnement_ext_pmr", False),
        ],
        # END DEPRECATED
        "Non, il y a une place de stationnement classique pas loin uniquement": [
            ("stationnement_ext_presence", True),
            ("stationnement_ext_pmr", False),
        ],
        "Non, il n'y a aucune place de stationnement pas loin": [
            ("stationnement_ext_presence", False),
        ],
        "Je ne suis pas sûr": [],
    },
    "Vous avez une rampe amovible : avez-vous aussi une sonnette pour appeler à l'intérieur ?": {
        "Oui": [("entree_dispositif_appel", True)],
        "Non": [("entree_dispositif_appel", False)],
    },
    "Avez-vous un parking réservé à vos visiteurs ?": {
        "Oui, nous avons un parking réservé": [("stationnement_presence", True), ("cheminement_ext_presence", True)],
        "Non, nous n'avons pas de parking réservé": [("stationnement_presence", False)],
        "Je ne sais pas": [],
    },
    "Est-ce qu’il y a des toilettes adaptées dans votre établissement ?": {
        "Oui, j'ai des toilettes adaptées": [("sanitaires_presence", True), ("sanitaires_adaptes", True)],
        "Non, ce sont des toilettes classiques": [("sanitaires_presence", True), ("sanitaires_adaptes", False)],
        "Je n'ai pas de toilettes": [("sanitaires_presence", False)],
        "Je ne suis pas sûr": [],
    },
    "Avez-vous une rampe d'accès pour entrer dans votre établissement ?": {
        "Oui, j'ai une rampe fixe": [("entree_marches_rampe", "fixe")],
        "Oui, j'ai une rampe amovible": [("entree_marches_rampe", "amovible")],
        "Non, pas de rampe": [("entree_marches_rampe", "aucune")],
        "Autre": [],
        "Je ne suis pas sûr": [],
    },
    "Est-ce qu'il faut, pour entrer dans votre établissement, monter les marches ou les descendre ?": {
        "Je dois monter le(s) marche(s)": [("entree_marches_sens", "montant")],
        "Je dois descendre le(s) marche(s)": [("entree_marches_sens", "descendant")],
        "Autre": [],
        "Je ne suis pas sûr": [],
    },
    "Est-ce que le chemin pour aller de votre place de parking handicapé jusqu'à l'entrée est praticable par un fauteuil roulant ?": {
        "Oui c'est praticable": [
            ("cheminement_ext_presence", True),
            ("cheminement_ext_terrain_stable", True),
            ("cheminement_ext_plain_pied", True),
            ("cheminement_ext_retrecissement", False),
        ],
        "Non, ce n'est pas praticable": [("cheminement_ext_presence", True)],
        "Je ne suis pas sûr": [],
    },
}
if hosting:
    mapping |= {
        "La douche est-elle utilisable par une personne en fauteuil roulant, (c'est à dire à l'italienne ou équipée d'un bac extra plat) ?": {
            "Douche à l'italienne ou équipée d'un bac extra plat": [("accueil_chambre_douche_plain_pied", True)],
            "Non": [("accueil_chambre_douche_plain_pied", False)],
        },
        "Un accompagnement personnalisé pour présenter la chambre à un client en situation de handicap, notamment aveugle ou malvoyant est-il possible ? ": {
            "Oui": [("accueil_chambre_accompagnement", True)],
            "Non": [("accueil_chambre_accompagnement", False)],
            "Je ne suis pas sûr": [],
        },
        "L'établissement dispose t-il d'un ou plusieurs équipements d'alerte par flash lumineux ou vibration ?": {
            "Oui": [("accueil_chambre_equipement_alerte", True)],
            "Non": [("accueil_chambre_equipement_alerte", False)],
            "Je ne suis pas sûr": [],
        },
        "Les numéros de chambres sont-ils facilement repérables et en relief ?": {
            "Oui": [("accueil_chambre_numero_visible", True)],
            "Non": [("accueil_chambre_numero_visible", False)],
            "Je ne suis pas sûr": [],
        },
    }
    to_ignore_headers += [
        "Avez-vous des chambres pour accueillir des clients dans votre établissement ?",
    ]

if culture:
    mapping |= {
        # TEMP entree_porte, will disappear with new templated forms
        "Comment s'ouvre la porte ?": {
            "Porte coulissante": [("entree_porte_presence", True), ("entree_porte_manoeuvre", "coulissante")],
            "Porte battante": [("entree_porte_presence", True), ("entree_porte_manoeuvre", "battante")],
            "Porte tourniquet": [("entree_porte_presence", True), ("entree_porte_manoeuvre", "tourniquet")],
            "Porte tambour": [("entree_porte_presence", True), ("entree_porte_manoeuvre", "tambour")],
            "Autre": [("entree_porte_presence", True)],
        },
        "Quel est le type de porte ?": {
            "Manuelle": [("entree_porte_presence", True), ("entree_porte_type", "manuelle")],
            "Automatique": [("entree_porte_presence", True), ("entree_porte_type", "automatique")],
            "Autre": [("entree_porte_presence", True)],
        },
        "Existe-t-il un dispositif pour permettre à quelqu'un signaler sa présence à l'entrée ?": {
            "Oui": [("entree_dispositif_appel", True)],
            "Non": [("entree_dispositif_appel", False)],
            "Je ne sais pas": [],
        },
        "Quel(s) type(s) de dispositifs d'appel sont présents ?": {
            "Bouton d'appel": [("entree_dispositif_appel_type", "bouton")],
            "Interphone": [("entree_dispositif_appel_type", "interphone")],
            "Visiophone": [("entree_dispositif_appel_type", "visiophone")],
        },
        "En cas de présence du personnel, est-il formé ou sensibilisé à l'accueil des personnes handicapées ?": {
            "Oui": [("accueil_personnels", "formés")],
            "Non": [("accueil_personnels", "non-formés")],
            "Aucun personnel": [("accueil_personnels", "aucun")],
            "Je ne sais pas": [],
        },
        # ENDTEMP
        "L'établissement propose-t-il de l'audiodescription ?": {
            "Oui": [("accueil_audiodescription_presence", True)],
            "Non": [("accueil_audiodescription_presence", False)],
            "Je ne sais pas": [],
        },
        "sans équipement, audiodescription audible par toute la salle (selon la programmation)": {
            "true": [("accueil_audiodescription", ["sans_équipement"])],
            "false": [],
        },
        "avec équipement permanent, casques et boîtiers disponibles à l'accueil": {
            "true": [("accueil_audiodescription", ["avec_équipement_permanent"])],
            "false": [],
        },
        "avec équipement permanent nécessitant le téléchargement d'une application sur smartphone": {
            "true": [("accueil_audiodescription", ["avec_app"])],
            "false": [],
        },
        "avec équipement occasionnel selon la programmation": {
            "true": [("accueil_audiodescription", ["avec_équipement_occasionnel"])],
            "false": [],
        },
        "L'accueil est-il équipé de produits ou prestations dédiés aux personnes sourdes ou malentendantes ?": {
            "Oui": [("accueil_equipements_malentendants_presence", True)],
            "Non": [("accueil_equipements_malentendants_presence", False)],
            "Je ne sais pas": [],
        },
        "Langue française parlée complétée (LFPC)": {
            "true": [("accueil_equipements_malentendants", ["lpc"])],
            "false": [],
        },
        "Boucle à induction magnétique portative": {
            "true": [("accueil_equipements_malentendants", ["bmp"])],
            "false": [],
        },
        "Boucle à induction magnétique fixe": {
            "true": [("accueil_equipements_malentendants", ["bim"])],
            "false": [],
        },
        "Langue des signes française (LSF)": {
            "true": [("accueil_equipements_malentendants", ["lsf"])],
            "false": [],
        },
        "Sous-titrage ou transcription simultanée": {
            "true": [("accueil_equipements_malentendants", ["sts"])],
            "false": [],
        },
        "Autre": {
            "true": [("accueil_equipements_malentendants", ["autres"])],
            "false": [],
        },
    }
    to_ignore_headers += [
        "type d'équipements pour l'audiodescription",
        "liste des équipements d'aide à l'audition et à la communication ?",
    ]
if ath:
    mapping |= {
        "Quelle est votre marque Tourisme &amp; handicap ? (Handicap Auditif)": {
            "true": [("labels", ["th"]), ("labels_familles_handicap", ["auditif"])],
            "false": [("labels", ["th"])],
        },
        "Quelle est votre marque Tourisme &amp; handicap ? (Handicap Mental)": {
            "true": [("labels", ["th"]), ("labels_familles_handicap", ["mental"])],
            "false": [("labels", ["th"])],
        },
        "Quelle est votre marque Tourisme &amp; handicap ? (Handicap Moteur)": {
            "true": [("labels", ["th"]), ("labels_familles_handicap", ["moteur"])],
            "false": [("labels", ["th"])],
        },
        "Quelle est votre marque Tourisme &amp; handicap ? (Handicap Visuel)": {
            "true": [("labels", ["th"]), ("labels_familles_handicap", ["visuel"])],
            "false": [("labels", ["th"])],
        },
    }
    to_ignore_headers += ["Quelle est votre marque Tourisme &amp; handicap ?"]

to_int_headers = {
    "Combien de marches y a-t-il pour entrer dans votre établissement ?": "entree_marches",
}
if hosting:
    to_int_headers |= {
        "Combien de chambres accessibles avez-vous dans votre établissement ?": "accueil_chambre_nombre_accessibles",
    }


kept_headers = {
    "nom": "nom",
    "adresse": "adresse",
}
basic_mapped_headers = {
    "email": "import_email",
    "cp": "code_postal",
    "ville": "commune",
}
if with_comment:
    basic_mapped_headers |= {
        "Informations complémentaires": "commentaire",
    }

if with_activity:
    basic_mapped_headers |= {
        "Quelle est l'activité de votre établissement ?": "activite",
    }
if with_siret:
    basic_mapped_headers |= {
        "Votre Siret (facultatif)": "siret",
    }


class Command(BaseCommand):
    help = "Convert from a tally format to a schema format."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Chemin du fichier à traiter, CSV avec séparateur virgule",
        )

    def _do_geocode(self, address, cp):
        try:
            geo_info = geocode(address, postcode=cp)
        except Exception as e:
            print(f"Erreur géocodage : {e}")
            return None
        return geo_info

    def _process_line(self, line):
        new_line = line.copy()
        for cell in line:
            line[cell] = BaseMapper.format_data(line[cell])

            if cell in kept_headers:
                continue

            if cell in mapping:
                try:
                    if line[cell] and mapping[cell][line[cell]]:
                        for k, v in mapping[cell][line[cell]]:
                            if isinstance(v, (list, set, tuple)):
                                new_line[k] = set(new_line.get(k) or [])
                                new_line[k] = new_line[k].union(set(v))
                                new_line[k] = list(new_line[k])
                            else:
                                new_line[k] = v
                except KeyError:
                    print(f"ERROR - {cell} -> {line[cell]} not found in {mapping[cell]}")
                    return

            elif cell in to_int_headers:
                try:
                    new_line[to_int_headers[cell]] = int(line[cell])
                except (ValueError, TypeError):
                    pass

            elif cell in basic_mapped_headers:
                new_line[basic_mapped_headers[cell]] = line[cell]

            new_line.pop(cell, None)

        new_line["source"] = Erp.SOURCE_TALLY
        new_line["code_postal"] = BaseMapper.handle_5digits_code(new_line["code_postal"])
        geo = self._do_geocode(new_line["adresse"], new_line["code_postal"])
        if geo:
            for attr in ("numero", "voie", "lieu_dit", "code_postal", "commune", "code_insee"):
                new_line[attr] = geo[attr]
        new_line.pop("adresse")
        return new_line

    def handle(self, *args, **options):
        self.input_file = options.get("file")

        expected_headers = (
            list(mapping.keys())
            + list(to_int_headers)
            + list(kept_headers.keys())
            + list(basic_mapped_headers.keys())
            + to_ignore_headers
        )

        with open(self.input_file, mode="r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if set(expected_headers) != set(reader.fieldnames):
                missing = set(expected_headers) - set(reader.fieldnames)
                extra = set(reader.fieldnames) - set(expected_headers)
                print(f"ERROR - Invalid headers, missing {missing} or extra headers: {extra}.")
                return

            with open(self.input_file.replace(".csv", "_converted.csv"), "w") as new_file:
                writer = csv.DictWriter(new_file, fieldnames=BaseMapper.fields + ["source"])
                writer.writeheader()

                for line in reader:
                    new_line = self._process_line(line)
                    for cell in new_line:
                        if isinstance(new_line[cell], (list, set, tuple)):
                            new_line[cell] = json.dumps(new_line[cell])
                    writer.writerow(new_line)
