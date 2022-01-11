import os

from django.core.management.base import BaseCommand

from core.lib import geo
from erp.models import Activite, Erp, Accessibilite, Commune
from xml.etree import ElementTree as ET

from erp.provider import arrondissements

VALEURS_VIDES = [
    "nr",
    "non renseigné",
    "non renseignée",
    "Non renseigné(e)",
    "#N/A",
]


def clean(string):
    if string in VALEURS_VIDES:
        return ""
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


def extract(xml, fieldname=None, attribute=None):
    if fieldname:
        field = xml.find(f"{fieldname}")
    else:
        field = xml
    if field is not None and not attribute:
        string = field.text
    else:
        if hasattr(field, "attrib"):
            string = field.attrib[attribute]
        else:
            return ""
    return clean(string)


def extract_adresse(xml, fieldname):
    fields = xml.findall(f"{fieldname}")
    num = lieu_dit = ligne = None

    if len(fields) > 1:
        lieu_dit = fields[0].text
        try:
            num, ligne = fields[1].text.split(None, 1)
        except Exception:
            ligne = fields[1].text
    elif len(fields) == 1:
        lieu_dit = None
        try:
            num, ligne = fields[0].text.split(None, 1)
        except Exception:
            ligne = fields[0].text
    return num, ligne, lieu_dit


class Command(BaseCommand):
    help = "Importe les données Service Public"

    def add_arguments(self, parser):
        parser.add_argument(
            "--forceupdate",
            action="store_true",
            help="Forcer la mise à jour de la fiche ERP.",
        )

    def handle_5digits_code(self, cpost):
        cpost = clean(cpost).strip()
        if len(cpost) == 4:
            return "0" + cpost
        return cpost

    def import_row(self, xml, **kwargs):
        fields = {}
        fields["nom"] = extract(xml, fieldname="Nom")
        fields["telephone"] = extract(xml, fieldname="*Téléphone")
        fields["contact_email"] = extract(xml, fieldname="*Email")
        fields["site_internet"] = extract(xml, fieldname="*Url")

        fields["code_insee"] = self.handle_5digits_code(
            extract(xml, attribute="codeInsee")
        )
        num, voie, lieu_dit = extract_adresse(xml, fieldname="*Ligne")
        fields["numero"] = num
        fields["lieu_dit"] = lieu_dit
        fields["voie"] = voie
        fields["code_postal"] = self.handle_5digits_code(
            extract(xml, fieldname="*CodePostal")
        )
        fields["commune"] = clean_commune(extract(xml, fieldname="*NomCommune"))
        fields["commune_ext_id"] = self._retrieve_commune_ext(
            commune=fields["commune"],
            code_insee=fields["code_insee"],
            code_postal=fields["code_postal"],
        )
        lat = extract(xml, fieldname="**Latitude")
        long = extract(xml, fieldname="**Longitude")
        if lat != "None" and long != "None" and (lat and long):
            fields["geom"] = geo.parse_location((lat, long))
        else:
            return None
        nom_activite = extract(xml, attribute="pivotLocal")
        if nom_activite:
            for (pka, activite) in self.activites:
                if nom_activite.lower().strip() == activite:
                    fields["activite_id"] = pka

        # checks rest
        if any(
            [
                fields["nom"] == "",
                fields["code_postal"] == "",
                fields["commune"] == "",
                fields["voie"] == "" and fields["lieu_dit"] == "",
                fields["geom"] == "",
                "activite_id" not in fields,
            ]
        ):
            return None

        erp = None
        # check doublons
        try:
            erp = Erp.objects.get(
                nom=fields["nom"],
                voie=fields["voie"],
                commune=fields["commune"],
                activite__pk=fields["activite_id"],
            )
        except Erp.MultipleObjectsReturned:
            # des doublons existent déjà malheureusement :(
            return None
        except Erp.DoesNotExist:
            pass

        if erp and self.force_update:
            Erp.objects.filter(pk=erp.pk).update(**fields)
            erp.refresh_from_db()

        return erp if erp else Erp(**fields)

    def get_xml_dirpath(self):
        here = os.path.abspath(
            os.path.join(os.path.abspath(__file__), "..", "..", "..")
        )
        return os.path.join(
            os.path.dirname(here), "data", "service-public", "organismes"
        )

    def _retrieve_commune_ext(self, commune, code_insee=None, code_postal=None):
        "Assigne une commune normalisée à l'Erp en cours de génération"
        if code_insee:
            commune_ext = Commune.objects.filter(code_insee=code_insee).first()
            if not commune_ext:
                arrdt = arrondissements.get_by_code_insee(code_insee)
                if arrdt:
                    commune_ext = Commune.objects.filter(
                        nom__iexact=arrdt["commune"]
                    ).first()
        elif code_postal:
            commune_ext = Commune.objects.filter(
                code_postaux__contains=[code_postal]
            ).first()
        else:
            raise RuntimeError(
                f"Champ code_insee et code_postal nuls (commune: {commune})"
            )

        if not commune_ext:
            print(
                f"Impossible de résoudre la commune depuis le code INSEE ({code_insee}) "
                f"ou le code postal ({code_postal}) "
            )
            return None
        return commune_ext.pk

    def get_access(self, xml):
        data = {}
        access = xml.find("*Accessibilité")
        if access is not None and access.attrib:
            if access.attrib["type"] == "ACC":
                if access.text is None:
                    data["commentaire"] = "Établissement accessible en fauteuil roulant"
                else:
                    if "plain pied" in access.text:
                        data["entree_plain_pied"] = True

                    if "rampe" in access.text:
                        data["entree_plain_pied"] = False
                        data["entree_marches_rampe"] = "fixe"
            elif access.attrib["type"] == "NAC":
                data["entree_plain_pied"] = False
            elif access.attrib["type"] == "DEM":
                data["entree_plain_pied"] = False
                data["entree_marches_rampe"] = "amovible"
                data["entree_aide_humaine"] = True

        return data

    def handle(self, *args, **options):
        self.force_update = options.get("forceupdate")
        self.add_files()
        self.parse_files()
        print("Importation effectuée.")
        print(f"{len(self.all_files)} fichiers")
        print(f"{self.imported_erps} erps importés")
        print(f"{self.existed_erps} erps déjà existants")
        print(f"{self.erps_with_access_changed} erps avec données d'access modifiées")

    def add_files(self):
        csv_dirpath = self.get_xml_dirpath()
        self.stdout.write(f"Récupération des fichiers depuis {csv_dirpath}")

        list_dir = os.listdir(csv_dirpath)
        self.stdout.write(f"{len(list_dir)} dossier(s) à traiter")

        self.all_files = []
        self.imported_erps = 0
        self.existed_erps = 0
        self.erps_with_access_changed = 0
        for root, directories, files in os.walk(csv_dirpath, topdown=False):
            for name in files:
                path_file = os.path.join(root, name)
                if os.path.splitext(path_file)[-1] == ".xml":
                    self.all_files.append(path_file)
        self.stdout.write(f"{len(self.all_files)} fichier(s) à traiter")

        self.activites = [(a.pk, a.nom.lower().strip()) for a in Activite.objects.all()]

    def parse_files(self):
        for f in self.all_files:
            self.stdout.write(f"{f}")
            tree = ET.parse(f)
            root = tree.getroot()
            try:
                data_access = self.get_access(root)
            except Exception as e:
                self.stdout.write(f"Access Data Error : {e}")
                raise e
            try:
                erp = self.import_row(root)
            except Exception as e:
                self.stdout.write(f"ERP Data Error : {e}")
                raise e
            else:
                if erp and data_access:
                    if hasattr(erp, "pk") and erp.pk:
                        self.existed_erps += 1
                        print(
                            f"EXIST {erp.nom} {erp.voie} {erp.commune} {self.force_update}"
                        )
                        if self.force_update:
                            print("\tUPDATE FORCED on this ERP")
                            erp.save()
                    else:
                        erp.save()
                        print(f"ADD {erp}")
                        self.imported_erps += 1
                        if not hasattr(erp, "accessibilite"):
                            erp.accessibilite = Accessibilite(**data_access)
                            erp.accessibilite.save()
                            self.erps_with_access_changed += 1
