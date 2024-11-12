import logging
from datetime import datetime

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance

from erp.imports.mapper.generic import GenericMapper
from erp.models import Accessibilite, Erp, ExternalSource

logger = logging.getLogger(__name__)


class NestennMapper(GenericMapper):
    erp = None
    fields = [
        "id",
        "siret",
        "name",
        "code_insee",
        "postal_code",
        "voie",
        "longitude",
        "latitude",
        "contact_url",
        "site_internet",
        "commune",
        "numero",
        "lieu_dit",
        "activite",
    ]

    def __init__(self, record, activite=None, today=None):
        self.record = record
        self.today = today if today is not None else datetime.today()
        self.activite = activite

    def process(self):
        try:
            basic_fields = self._extract_basic_fields(self.record)
        except ValueError as e:
            print(e)
            return None, None
        # check for a preexisting match (before we had imports)
        # erp = self._process_preexisting(basic_fields["geom"])
        erp = None
        # already imported erps
        if not erp:
            erp = Erp.objects.find_by_source_id(ExternalSource.SOURCE_NESTENN, self.record["id"]).first()

        # new erp
        if not erp:
            erp = Erp(
                source=ExternalSource.SOURCE_NESTENN,
                source_id=self.record["id"],
                activite=self.activite,
            )

        self.erp = erp
        for name, value in basic_fields.items():
            setattr(self.erp, name, value)

        self.erp.save()
        self._retrieve_commune_ext()
        self._populate_accessibilite()

        return self.erp, None

    def _process_preexisting(self, location):
        erp = (
            Erp.objects.exclude(source=ExternalSource.SOURCE_NESTENN)
            .filter(
                activite=self.activite,
                geom__distance_lte=(location, Distance(m=2000)),
            )
            .first()
        )
        if erp:
            # unpublish already imported duplicate
            old_erp = Erp.objects.find_by_source_id(
                ExternalSource.SOURCE_NESTENN,
                self.record["id"],
                published=True,
            ).first()
            if old_erp:
                old_erp.published = False
                old_erp.save()
                logger.info(f"Unpublished obsolete duplicate: {str(old_erp)}")
            # update preexisting erp with new import information
            erp.source = ExternalSource.SOURCE_NESTENN
            erp.source_id = self.record["id"]
        return erp

    def _import_coordinates(self, record):
        "Importe les coordonnées géographiques."
        try:
            x, y = float(record["longitude"]), float(record["latitude"])
            return Point(x, y, srid=4326)
        except (KeyError, IndexError):
            raise RuntimeError("Coordonnées géographiques manquantes ou invalides")
        except ValueError as e:
            print(e)

    def _handle_5digits_code(self, record, cpost):
        cpost = cpost.strip()
        if len(cpost) == 5:
            return cpost
        if not cpost or len(cpost) != 4:
            raise ValueError(f"Code invalide : {cpost} (record {record})")
        if len(cpost) == 4:
            return "0" + cpost
        return cpost

    def _extract_basic_fields(self, record):
        try:
            return {
                "code_insee": self._handle_5digits_code(record, record["code_insee"]),
                "code_postal": self._handle_5digits_code(record, record["postal_code"]),
                "numero": record.get("numero"),
                "voie": record["voie"],
                "geom": self._import_coordinates(record),
                "site_internet": record["site_internet"],
                "siret": record.get("siret"),
                "nom": record["name"],
                "contact_url": record["contact_url"],
            }
        except KeyError as key:
            raise RuntimeError(f"Impossible d'extraire des données: champ {key} manquant")

    def _get_typed_value(self, value, type_str):
        if type_str == "nullboolean":
            if not value:
                return None
            return True if value in ["True", "true"] else False

    def _build_a11y(self, erp, data):
        data_a11y = dict()
        data_a11y["transport_station_presence"] = self._get_typed_value(
            data["transport_station_presence"], "nullboolean"
        )
        data_a11y["stationnement_ext_presence"] = self._get_typed_value(
            data["transport_station_presence"], "nullboolean"
        )
        data_a11y["entree_balise_sonore"] = self._get_typed_value(data["transport_station_presence"], "nullboolean")
        data_a11y["entree_aide_humaine"] = self._get_typed_value(data["transport_station_presence"], "nullboolean")
        data_a11y["entree_porte_presence"] = self._get_typed_value(data["transport_station_presence"], "nullboolean")

        data_a11y["commentaire"] = self._build_comment()
        return Accessibilite(erp=erp, **data_a11y)

    def _populate_accessibilite(
        self,
    ):
        if not self.erp.has_accessibilite():
            accessibilite = self._build_a11y(erp=self.erp, data=self.record)
            accessibilite.save()
            self.erp.accessibilite = accessibilite
            self.erp.save()

    def _build_comment(self):
        date = self.today.strftime("%d/%m/%Y")
        comment = f"Ces informations ont été importées le {date} "
        return comment.rstrip()
