from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Activite, Erp


VILLES_CIBLES = ["rueil-malmaison", "courbevoie", "lorient"]


class ErpResource(resources.ModelResource):
    class Meta:
        model = Erp
        skip_unchanged = True
        exclude = (
            "id",
            "telephone",
            "site_internet",
            "created_at",
            "updated_at",
        )

    def handle_5digits_code(self, cpost):
        cpost = str(cpost)
        if len(cpost) == 4:
            return "0" + cpost
        return cpost

    def handle_siret(self, siret):
        siret = str(siret).strip()
        if len(siret) == 14 and siret.isdigit():
            return siret
        else:
            return None

    def before_import_row(self, row, **kwargs):
        # siret
        row["siret"] = self.handle_siret(row["siret"])
        # adresse
        if row["cplt"] == "" or row["cplt"] == "NR":
            cplt = ""
        else:
            cplt = row["cplt"]
        row["numero"] = row["num"] + " " + cplt
        row["code_postal"] = self.handle_5digits_code(row["cpost"])
        row["code_insee"] = self.handle_5digits_code(row["code_insee"])

        # activité
        nom_activite = row["domaine"]
        try:
            activite = Activite.objects.get(nom=nom_activite).pk
        except Activite.DoesNotExist:
            activite = None
        row["activite"] = activite

    def skip_row(self, instance, original):
        if any(
            [
                instance.nom.strip() == "",
                instance.code_postal.strip() == "",
                instance.commune.strip() == "",
                instance.voie.strip() == "" and instance.lieu_dit.strip() == "",
                instance.commune.lower().strip() not in VILLES_CIBLES,
                instance.geom is None,
            ]
        ):
            return True
        return super(ErpResource, self).skip_row(instance, original)
