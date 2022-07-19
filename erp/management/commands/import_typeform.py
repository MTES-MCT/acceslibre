import csv
import os
import sys

from django.core.management.base import BaseCommand

from erp.models import Activite, Erp, Commune, Accessibilite
from erp.provider.geocoder import geocode


def clean(string):
    return (
        str(string)
        .replace("\n", " ")
        .replace("«", "")
        .replace("»", "")
        .replace("’", "'")
        .replace('"', "")
        .strip()
    )


def clean_commune(string):
    return clean("".join(i for i in string if not i.isdigit()))


class Command(BaseCommand):
    help = "Importe les données typeform"
    doublons = []

    def handle_5digits_code(self, cpost):
        cpost = clean(cpost).strip()
        if len(cpost) == 4:
            return "0" + cpost
        return cpost

    def import_row(self, row, **kwargs):
        fields = {}
        # nom
        fields["nom"] = "Mairie"
        try:
            lieu_dit, adresse = row["adresse"].split('", "')
        except Exception:
            adresse = row["adresse"]
            lieu_dit = None
        else:
            lieu_dit = lieu_dit.lstrip('["')
            adresse = adresse.rstrip('"]')
        try:
            geo_info = geocode(adresse, postcode=self.handle_5digits_code(row["cp"]))
        except Exception as e:
            error = f"Erreur géocodage : {e}"
            print(error)
            return None, None
        else:
            if not geo_info:
                error = "Adresse introuvable"
                print(error)
                return None, None

        code_insee = geo_info.get("code_insee")

        commune_ext = (
            Commune.objects.filter(code_insee=code_insee).first()
            if code_insee
            else None
        )

        fields["source"] = "typeform"
        fields["published"] = True
        fields["numero"] = geo_info.get("numero")
        fields["voie"] = geo_info.get("voie")
        fields["lieu_dit"] = lieu_dit
        fields["code_postal"] = geo_info.get("code_postal")
        fields["commune"] = geo_info.get("commune")
        fields["geom"] = geo_info.get("geom")
        fields["commune_ext"] = commune_ext
        fields["activite_id"] = Activite.objects.get(nom="Mairie").id

        # checks rest
        if any(
            [
                fields["nom"] == "",
                fields["code_postal"] == "",
                fields["commune"] == "",
                fields["voie"] == "" and fields["lieu_dit"] == "",
                fields["geom"] == "",
            ]
        ):
            return None, None

        # check doublons
        qs = Erp.objects.filter(
            numero=fields["numero"],
            voie__iexact=fields["voie"],
            commune__iexact=fields["commune"],
            code_insee=code_insee,
            activite__pk=fields["activite_id"],
        )
        if qs.count() >= 1:
            duplicated_pks = qs.values_list("pk", flat=True)
        else:
            duplicated_pks = []
        erp = Erp(**fields)
        erp.save()

        accessibilite = Accessibilite(erp=erp)

        field_label = "Votre mairie : {{hidden:nom}}  Y-a-t il une marche (ou plus) pour y rentrer ? (même toute petite)"
        if field_label in row:
            if row[field_label] == "Non, c'est de plain-pied":
                accessibilite.entree_plain_pied = True
            elif row[field_label] == "Oui, au moins une marche":
                accessibilite.entree_plain_pied = False

        field_label = "Combien de marches y a t-il pour entrer dans votre mairie ?"
        if field_label in row:
            if row[field_label] != "":
                try:
                    int(row[field_label])
                except Exception:
                    print("Type of value is not conform : int expected")
                else:
                    accessibilite.entree_marches = int(row[field_label])

        field_label = "Est-ce qu'il faut, pour entrer dans la mairie, monter les marches ou les descendre ?"
        if field_label in row:
            if row[field_label] == "Je dois monter le(s) marche(s)":
                accessibilite.entree_marches_sens = "montant"
            elif row[field_label] == "je dois descendre le(s) marche(s)":
                accessibilite.entree_marches_sens = "descendant"

        field_label = "Avez-vous une rampe d'accès pour entrer dans votre mairie ?"
        if field_label in row:
            if row[field_label] == "Oui, j'ai une rampe fixe":
                accessibilite.entree_marches_rampe = "fixe"
            elif row[field_label] == "Oui, j'ai une rampe amovible":
                accessibilite.entree_marches_rampe = "amovible"
            elif row[field_label] == "Non, pas de rampe":
                accessibilite.entree_marches_rampe = "aucune"

        field_label = "Vous avez une rampe amovible : avez-vous aussi une sonnette pour appeler à l'intérieur ?"
        if field_label in row:
            if row[field_label] == "True":
                accessibilite.entree_dispositif_appel = True
            elif row[field_label] == "False":
                accessibilite.entree_dispositif_appel = False

        field_label = "Est-ce qu’il y a des toilettes adaptées dans votre mairie ?"
        if field_label in row:
            if row[field_label] == "Oui, j'ai des toilettes adaptées":
                accessibilite.sanitaires_presence = True
                accessibilite.sanitaires_adaptes = True
            elif row[field_label] == "Non, ce sont des toilettes classiques":
                accessibilite.sanitaires_presence = True
                accessibilite.sanitaires_adaptes = False
            elif row[field_label] == "Je n'ai pas de toilettes":
                accessibilite.sanitaires_presence = False

        field_label = "Avez-vous un parking réservé à vos administrés?"
        if field_label in row:
            if row[field_label] == "Oui, nous avons un parking reservé":
                accessibilite.stationnement_presence = True
            elif row[field_label] == "Non, nous n'avons pas de parking reservé":
                accessibilite.stationnement_presence = False

        field_label = "Est-ce qu’il y au moins une place handicapé dans votre parking ?"
        if field_label in row:
            if row[field_label] == "Oui c'est praticable":
                accessibilite.cheminement_ext_presence = True
                accessibilite.cheminement_ext_terrain_stable = True
                accessibilite.cheminement_ext_plain_pied = True
                accessibilite.cheminement_ext_retrecissement = False
            elif row[field_label] == "Non, ce n'est pas praticable":
                accessibilite.cheminement_ext_presence = True

        field_label = "Ce chemin n'est pas praticable car :"
        if field_label in row:
            if row[field_label] == "problème de pente":
                accessibilite.cheminement_ext_pente_presence = True
                accessibilite.cheminement_ext_pente_degre_difficulte = "importante"
                accessibilite.cheminement_ext_pente_longueur = "longue"
            elif row[field_label] == "problème de marche":
                accessibilite.cheminement_ext_plain_pied = False
                accessibilite.cheminement_ext_ascenseur = False
                accessibilite.cheminement_ext_rampe = "aucune"

        field_label = "Est-ce qu’il y au moins une place handicapé dans les environs ?"
        if field_label in row:
            if (
                row[field_label]
                == "Oui, il y a une place  de parking handicapé pas loin"
            ):
                accessibilite.stationnement_ext_presence = True
                accessibilite.stationnement_ext_pmr = True
            elif row[field_label] == "Non, pas de place handicapé pas loin":
                accessibilite.stationnement_ext_presence = True
                accessibilite.stationnement_ext_pmr = False
        accessibilite.save()
        return erp, duplicated_pks

    def get_csv_path(self):
        here = os.path.abspath(
            os.path.join(os.path.abspath(__file__), "..", "..", "..")
        )
        return os.path.join(
            os.path.dirname(here),
            "data",
            "Mairies.tsv",
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mode test",
        )

    def handle(self, *args, **options):
        csv_path = self.get_csv_path()
        self.to_import = []
        self.stdout.write(f"Importation des ERP depuis {csv_path}")
        with open(csv_path, "r") as file:
            reader = csv.DictReader(file, delimiter="\t")
            try:
                for row in reader:
                    erp, duplicated_pks = self.import_row(row)
                    if erp:
                        self.to_import.append(erp)
                    if duplicated_pks:
                        print(f"Add duplicate: {duplicated_pks}")
                        self.doublons.append(
                            (f"{row['cp']} - {row['nom']}", duplicated_pks)
                        )

            except csv.Error as err:
                sys.exit(f"file {csv_path}, line {reader.line_num}: {err}")
        if len(self.to_import) == 0:
            print("Rien à importer.")
        else:
            print(f"{len(self.to_import)} ERP à importer")
        if len(self.doublons) != 0:
            print(f"Doublons détectés ({len(self.doublons)}): {self.doublons}")
