import json


class BaseMapper:
    erp = None
    erp_fields = [
        "id",
        "nom",
        "code_postal",
        "commune",
        "numero",
        "voie",
        "lieu_dit",
        "code_insee",
        "siret",
        "activite",
        "contact_url",
        "site_internet",
        "longitude",
        "latitude",
        "import_email",
    ]

    accessibility_fields = [
        "transport_station_presence",
        "stationnement_presence",
        "stationnement_pmr",
        "stationnement_ext_presence",
        "stationnement_ext_pmr",
        "cheminement_ext_presence",
        "cheminement_ext_terrain_stable",
        "cheminement_ext_plain_pied",
        "cheminement_ext_ascenseur",
        "cheminement_ext_nombre_marches",
        "cheminement_ext_reperage_marches",
        "cheminement_ext_sens_marches",
        "cheminement_ext_main_courante",
        "cheminement_ext_rampe",
        "cheminement_ext_pente_presence",
        "cheminement_ext_pente_degree_difficulte",
        "cheminement_ext_pente_longueur",
        "cheminement_ext_devers",
        "cheminement_ext_bande_guidage",
        "cheminement_ext_retrecissement",
        "entree_reperage",
        "entree_vitree",
        "entree_vitree_vitrophanie",
        "entree_plain_pied",
        "entree_ascenseur",
        "entree_marches",
        "entree_marches_reperage",
        "entree_marches_main_courante",
        "entree_marches_rampe",
        "entree_marches_sens",
        "entree_dispositif_appel",
        "entree_dispositif_appel_type",
        "entree_balise_sonore",
        "entree_aide_humaine",
        "entree_largeur_mini",
        "entree_pmr",
        "entree_porte_presence",
        "entree_porte_manoeuvre",
        "entree_porte_type",
        "acceuil_visibilite",
        "acceuil_personnels",
        "accueil_audiodescription_presence",
        "accueil_audiodescription",
        "accueil_equipements_malentendants_presence",
        "accueil_equipements_malentendants",
        "accueil_cheminement_plain_pied",
        "accueil_cheminement_ascenseur",
        "accueil_cheminement_nombre_marches",
        "accueil_cheminement_reperage_marches",
        "accueil_cheminement_main_courante",
        "accueil_cheminement_rampe",
        "accueil_cheminement_sens_marches",
        "accueil_retrecissement",
        "sanitaires_presence",
        "sanitaires_adaptes",
        "labels",
        "labels_familles_handicap",
        "registre_url",
        "conformite",
    ]

    fields = erp_fields + accessibility_fields

    @staticmethod
    def clean(string):
        return (
            str(string).replace("\n", " ").replace("«", "").replace("»", "").replace("’", "'").replace('"', "").strip()
        )

    @staticmethod
    def handle_5digits_code(cpost):
        cpost = BaseMapper.clean(cpost).strip()
        if len(cpost) == 4:
            return "0" + cpost
        return cpost

    def format_data(self, value):
        if value == "":
            return None
        return value.strip()

    def csv_to_erp(self, record, *args, **kwargs):
        try:
            dest_fields = self.get_erp_fields(record, *args, **kwargs)
            dest_fields["accessibilite"] = self.get_a11y_fields(record)
        except KeyError as key:
            raise RuntimeError(f"Impossible d'extraire des données: champ {key} manquant")

        return dest_fields

    def get_erp_fields(self, record, *args, **kwargs):
        dest_fields = {k: self.format_data(v) for k, v in record.items() if k in self.erp_fields}
        dest_fields["nom"] = record.get("name")
        dest_fields["code_postal"] = record.get("postal_code")
        return dest_fields

    def get_a11y_fields(self, record):
        a11y_data = {k: self.format_data(v) for k, v in record.items() if k in self.accessibility_fields}
        a11y_data["labels"] = json.loads(record.get("labels")) if record.get("labels") else None
        a11y_data["labels_familles_handicap"] = (
            json.loads(record.get("labels_familles_handicap")) if record.get("labels_familles_handicap") else None
        )
        return a11y_data
