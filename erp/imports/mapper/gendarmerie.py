import re
import logging

from datetime import datetime

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance

from erp.models import Erp, Commune, Accessibilite
from erp.provider import arrondissements


logger = logging.getLogger(__name__)


class GendarmerieMapper:
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

    def __init__(self, record, activite=None, today=None):
        self.record = record
        self.today = today if today is not None else datetime.today()
        self.activite = activite

    def process(self):
        basic_fields = self._extract_basic_fields(self.record)

        # check for a preexisting match (before we had imports)
        erp = self._process_preexisting(basic_fields["geom"])

        # already imported erps
        if not erp:
            erp = Erp.objects.find_by_source_id(
                Erp.SOURCE_GENDARMERIE, self.record["identifiant_public_unite"]
            ).first()

        # new erp
        if not erp:
            erp = Erp(
                source=Erp.SOURCE_GENDARMERIE,
                source_id=self.record["identifiant_public_unite"],
                activite=self.activite,
            )

        self.erp = erp
        for name, value in basic_fields.items():
            setattr(self.erp, name, value)

        self._retrieve_commune_ext()
        self._populate_accessibilite(self.record)

        return self.erp, None

    def _process_preexisting(self, location):
        erp = (
            Erp.objects.exclude(source=Erp.SOURCE_GENDARMERIE)
            .filter(
                activite=self.activite,
                geom__distance_lte=(location, Distance(m=2000)),
            )
            .first()
        )
        if erp:
            # unpublish already imported duplicate
            old_erp = Erp.objects.find_by_source_id(
                Erp.SOURCE_GENDARMERIE,
                self.record["identifiant_public_unite"],
                published=True,
            ).first()
            old_erp.published = False
            old_erp.save()
            logger.info(f"Unpublished obsolete duplicate: {str(old_erp)}")
            # update preexisting erp with new import information
            erp.source = Erp.SOURCE_GENDARMERIE
            erp.source_id = self.record["identifiant_public_unite"]
        return erp

    def _parse_address(self, record):
        res = record["voie"].split(" ")
        try:
            if res[0][0].isdigit():
                numero = res[0]
                if res[1].lower() in ["bis", "ter"]:
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
            return Point(x, y, srid=4326)
        except (KeyError, IndexError):
            raise RuntimeError("Coordonnées géographiques manquantes ou invalides")

    def _extract_basic_fields(self, record):
        try:
            numero, voie = self._parse_address(record)
            return {
                "telephone": record["telephone"],
                "code_insee": record["code_commune_insee"],
                "code_postal": record["code_postal"],
                "numero": numero,
                "voie": voie,
                "geom": self._import_coordinates(record),
                "site_internet": record["url"],
                "nom": record["service"],
                "contact_url": "https://www.gendarmerie.interieur.gouv.fr/a-votre-contact/contacter-la-gendarmerie/magendarmerie.fr",
            }
        except KeyError as key:
            raise RuntimeError(
                f"Impossible d'extraire des données: champ {key} manquant"
            )

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
            raise RuntimeError(
                f"Impossible de résoudre la commune depuis le code INSEE ({self.erp.code_insee}) "
                f"ou le code postal ({self.erp.code_postal}) "
            )

        self.erp.commune_ext = commune_ext
        self.erp.commune = commune_ext.nom

    def _populate_accessibilite(self, record):
        if not self.erp.has_accessibilite():
            accessibilite = Accessibilite(erp=self.erp)
            self.erp.accessibilite = accessibilite
        self.erp.accessibilite.commentaire = self._build_comment(record)

    def _build_comment(self, record):
        date = self.today.strftime("%d/%m/%Y")
        comment = (
            f"Ces informations ont été importées depuis data.gouv.fr le {date} "
            "https://www.data.gouv.fr/fr/datasets/liste-des-unites-de-gendarmerie-accueillant-du-public-comprenant-leur-geolocalisation-et-leurs-horaires-douverture/"
        )
        horaires = [
            s.strip()
            for s in re.findall("[A-Z][^A-Z]*", record["horaires_accueil"].strip())
        ]
        if len(horaires) > 0:
            comment += "\n\nHoraires d'accueil: \n"
            for horaire in horaires:
                comment += horaire + "\n"
        return comment.rstrip()
