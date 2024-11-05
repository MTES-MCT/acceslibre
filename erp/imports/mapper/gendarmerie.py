import logging
import re
from datetime import datetime

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance

from erp.exceptions import PermanentlyClosedException
from erp.imports.mapper.generic import GenericMapper
from erp.models import Accessibilite, Erp, ExternalSource

logger = logging.getLogger(__name__)


class GendarmerieMapper(GenericMapper):
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
        self.today = today or datetime.today()
        self.activite = activite

    def process(self):
        basic_fields = self._extract_basic_fields(self.record)

        erp = self._process_preexisting(basic_fields["geom"])

        if not erp:
            erps = Erp.objects.find_by_source_id(
                ExternalSource.SOURCE_GENDARMERIE, self.record["identifiant_public_unite"]
            )
            try:
                self._ensure_not_permanently_closed(erps)
            except PermanentlyClosedException:
                return None, None
            erp = erps.first()

        # new erp
        if not erp:
            erp = Erp(
                source=ExternalSource.SOURCE_GENDARMERIE,
                source_id=self.record["identifiant_public_unite"],
                activite=self.activite,
            )

        self.erp = erp
        for name, value in basic_fields.items():
            setattr(self.erp, name, value)

        self._retrieve_commune_ext(self.record.get("commune"))
        self._populate_accessibilite(self.record)

        return self.erp, None

    def _process_preexisting(self, location):
        erp = (
            Erp.objects.exclude(source=ExternalSource.SOURCE_GENDARMERIE)
            .filter(
                activite=self.activite,
                geom__distance_lte=(location, Distance(m=2000)),
            )
            .first()
        )
        if erp:
            # unpublish already imported duplicate
            old_erp = Erp.objects.find_by_source_id(
                ExternalSource.SOURCE_GENDARMERIE,
                self.record["identifiant_public_unite"],
                published=True,
            ).first()
            if old_erp:
                old_erp.published = False
                old_erp.save()
                logger.info(f"Unpublished obsolete duplicate: {str(old_erp)}")
            # update preexisting erp with new import information
            erp.source = ExternalSource.SOURCE_GENDARMERIE
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
                "site_internet": record["url"].replace('"', ""),
                "nom": record["service"],
                "contact_url": "https://www.gendarmerie.interieur.gouv.fr/a-votre-contact/contacter-la-gendarmerie/magendarmerie.fr",
            }
        except KeyError as key:
            raise RuntimeError(f"Impossible d'extraire des données: champ {key} manquant")

    def _populate_accessibilite(self, record):
        if not self.erp.has_accessibilite():
            accessibilite = Accessibilite(erp=self.erp, entree_porte_presence=True)
            self.erp.accessibilite = accessibilite
        self.erp.accessibilite.commentaire = self._build_comment(record)

    def _build_comment(self, record):
        date = self.today.strftime("%d/%m/%Y")
        comment = (
            f"Ces informations ont été importées depuis data.gouv.fr le {date} "
            "https://www.data.gouv.fr/fr/datasets/liste-des-unites-de-gendarmerie-accueillant-du-public-comprenant-leur-geolocalisation-et-leurs-horaires-douverture/"
        )
        horaires = [s.strip() for s in re.findall("[A-Z][^A-Z]*", record["horaires_accueil"].strip())]
        if horaires:
            comment += "\n\nHoraires d'accueil: \n"
            for horaire in horaires:
                comment += horaire + "\n"
        return comment.rstrip()
