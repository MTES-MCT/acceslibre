import csv

from django.core.management.base import BaseCommand, CommandError

from erp.models import Activite, Erp


VILLES_CIBLES = ["lyon", "villeurbanne"]
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


class Command(BaseCommand):
    help = "Importe les données c-conforme"

    def add_arguments(self, parser):
        parser.add_argument("csv_path")

    def handle_5digits_code(self, cpost):
        cpost = clean(cpost).strip()
        if len(cpost) == 4:
            return "0" + cpost
        return cpost

    def handle_siret(self, siret):
        siret = clean(siret)
        if len(siret) == 14 and siret.isdigit():
            return siret

    def import_row(self, row, **kwargs):
        fields = {}

        # nom
        fields["nom"] = clean(row["nom"])

        # siret
        fields["siret"] = self.handle_siret(row["siret"])

        # adresse
        if row["cplt"] == "" or row["cplt"] == "NR":
            cplt = ""
        else:
            cplt = row["cplt"]
        fields["numero"] = clean(row["num"] + " " + cplt)
        fields["voie"] = clean(row["voie"])
        fields["lieu_dit"] = clean(row["lieu_dit"])
        fields["code_postal"] = self.handle_5digits_code(row["cpost"])
        fields["commune"] = clean(row["commune"])
        fields["code_insee"] = self.handle_5digits_code(row["code_insee"])

        # geom
        fields["geom"] = clean(row["geom"])

        # checks
        if any(
            [
                fields["commune"].lower() not in VILLES_CIBLES,
                fields["nom"] == "",
                fields["code_postal"] == "",
                fields["commune"] == "",
                fields["voie"] == "" and clean(row["lieu_dit"]) == "",
                fields["geom"] == "",
            ]
        ):
            return

        # activité
        nom_activite = clean(row["domaine"])
        if nom_activite:
            for (pka, activite) in self.activites:
                if nom_activite.lower().strip() == activite:
                    fields["activite_id"] = pka

        erp = Erp(**fields)
        if erp.activite is not None:
            act = f"\n    {erp.activite.nom}"
        else:
            act = ""
        print(f"ADD {erp.nom}{act}\n    {erp.adresse}")
        return erp

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        self.stdout.write(f"Importation des ERP depuis {csv_path}")
        to_import = []

        self.activites = [(a.pk, a.nom.lower()) for a in Activite.objects.all()]

        with open(csv_path, "r") as file:
            reader = csv.DictReader(file)
            try:
                for row in reader:
                    erp = self.import_row(row)
                    if erp is not None:
                        to_import.append(erp)
            except csv.Error as err:
                sys.exit(f"file {filename}, line {reader.line_num}: {err}")
        if len(to_import) == 0:
            print("Rien à importer.")
            exit(0)
        res = Erp.objects.bulk_create(to_import)
        print(res)
