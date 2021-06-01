import re
from datetime import datetime

from django.contrib.gis.geos import Point

from erp.import_datasets.base_mapper import BaseRecordMapper
from erp.import_datasets.fetcher_strategy import Fetcher
from erp.models import Activite, Erp, Commune, Accessibilite
from erp.provider import arrondissements


class RecordMapper(BaseRecordMapper):
    dataset_url = (
        "https://www.data.gouv.fr/fr/datasets/r/061a5736-8fc2-4388-9e55-8cc31be87fa0"
    )
    activite = "gendarmerie"
    erp = None
    fields = [
        "identifiant_public_unite",
        "telephone",
        "code_commune_insee",
        "code_postal",
        "voie",
        "geocodage_x_GPS",
        "geocodage_y_GPS",
        "url",
        "service",
        "horaires_accueil",
    ]

    def __init__(self, fetcher: Fetcher, dataset_url: str = dataset_url, today=None):
        self.today = today if today is not None else datetime.today()
        self.fetcher = fetcher

    def fetch_data(self):
        data = self.fetcher.fetch(self.dataset_url)

        if not all(field in self.fetcher.fieldnames for field in self.fields):
            raise RuntimeError("Missmatch fields in CSV")
        return data

    def process(self, record, activite: Activite) -> Erp:
        erp = Erp.objects.find_by_source_id(
            Erp.SOURCE_GENDARMERIE, record["identifiant_public_unite"]
        )
        if not erp:
            erp = Erp(
                source=Erp.SOURCE_GENDARMERIE,
                source_id=record["identifiant_public_unite"],
                activite=activite,
            )

        self.erp = erp
        self.populate_basic_fields(record)
        self._retrieve_commune_ext()
        self.populate_accessibilite(record)

        return erp

    def _parse_address(self, record):
        res = record["voie"].split(" ")
        try:
            if res[0][0].isdigit():
                numero = res[0]
                if res[1] in ["bis", "ter"]:
                    numero += " " + res[1]
                    voie = " ".join(res[2:])
                else:
                    voie = " ".join(res[1:])
            else:
                numero = None
                voie = record["voie"]
        except (KeyError, IndexError):
            numero = None
            voie = record["voie"]

        return numero, voie

    def _import_coordinates(self, record):
        "Importe les coordonnées géographiques du centre de vaccination"
        try:
            x, y = float(record["geocodage_x_GPS"]), float(record["geocodage_y_GPS"])
            return Point(x, y)
        except (KeyError, IndexError):
            raise RuntimeError("Coordonnées géographiques manquantes ou invalides")

    def populate_basic_fields(self, record):
        try:
            numero, voie = self._parse_address(record)

            self.erp.private_contact_email = None
            self.erp.telephone = record["telephone"]
            self.erp.code_insee = record["code_commune_insee"]
            self.erp.code_postal = record["code_postal"]
            self.erp.numero = numero
            self.erp.voie = voie
            self.erp.geom = self._import_coordinates(record)
            self.erp.site_internet = record["url"]
            self.erp.nom = record["service"]
        except (KeyError, IndexError) as err:
            raise RuntimeError("Impossible d'extraire des données: " + str(err))

    def _retrieve_commune_ext(self):
        "Assigne une commune normalisée à l'Erp en cours de génération"
        if self.erp.code_insee:
            commune_ext = Commune.objects.filter(code_insee=self.erp.code_insee).first()
            if not commune_ext:
                arrdt = arrondissements.get_by_code_insee(self.erp.code_insee)
                if arrdt:
                    commune_ext = Commune.objects.filter(
                        nom__iexact=arrdt["commune"]
                    ).first()
        elif self.erp.code_postal:
            commune_ext = Commune.objects.filter(
                code_postaux__contains=[self.erp.code_postal]
            ).first()
        else:
            raise RuntimeError(
                f"Champ code_insee et code_postal nuls (commune: {self.erp.commune})"
            )

        if not commune_ext:
            raise RuntimeError("Impossible de résoudre la commune: ")

        self.erp.commune_ext = commune_ext
        self.erp.commune = commune_ext.nom

    def populate_accessibilite(self, record):
        if not self.erp.has_accessibilite():
            accessibilite = Accessibilite(erp=self.erp)
            self.erp.accessibilite = accessibilite
        self.erp.accessibilite.commentaire = self._build_comment(record)

    def _build_comment(self, record):
        horaires = re.findall("[A-Z][^A-Z]*", record["horaires_accueil"].strip())
        stripped = [s.strip() for s in horaires]
        comment = "Horaires d'accueil: \n"
        for h in stripped:
            comment += h + "\n"
        return comment.rstrip()
