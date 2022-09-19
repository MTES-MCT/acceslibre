import logging

from datetime import datetime

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance

from erp.models import Erp, Commune, Accessibilite, Activite
from erp.provider import arrondissements
from erp.schema import get_type, get_nullable

logger = logging.getLogger(__name__)


class GenericMapper:
    erp = None
    erp_fields = [
        "id",
        "nom",
        "postal_code",
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

    def __init__(self, record, source=None, activite=None, today=None):
        self.record = record
        self.today = today if today is not None else datetime.today()
        self.activite = activite
        self.source = source

    def process(self):
        try:
            basic_fields = self._extract_basic_fields(self.record)
        except ValueError as e:
            print(e)
            return None, None
        except Exception as e:
            print(e)
            raise e
        # check for a preexisting match (before we had imports)
        # erp = self._process_preexisting(basic_fields["geom"])
        erp = None
        # already imported erps

        if not erp:
            erp = Erp.objects.find_by_source_id(self.source, self.record["id"]).first()

        # new erp
        if not erp:
            erp = Erp(
                source=self.source,
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
            Erp.objects.exclude(source=self.source)
            .filter(
                activite__iexact=self.activite,
                geom__distance_lte=(location, Distance(m=2000)),
            )
            .first()
        )
        if erp:
            # unpublish already imported duplicate
            old_erp = Erp.objects.find_by_source_id(
                self.source,
                self.record["id"],
                published=True,
            ).first()
            if old_erp:
                old_erp.published = False
                old_erp.save()
                logger.info(f"Unpublished obsolete duplicate: {str(old_erp)}")
            # update preexisting erp with new import information
            erp.source = self.source
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
            erp_basic_fields = {k: v for k, v in record.items() if k in self.erp_fields}
            erp_basic_fields["nom"] = record.get("name")
            erp_basic_fields["geom"] = self._import_coordinates(erp_basic_fields)
            erp_basic_fields["activite"] = Activite.objects.get(
                nom__iexact=erp_basic_fields["activite"]
            )
            erp_basic_fields["code_insee"] = self._handle_5digits_code(
                erp_basic_fields, erp_basic_fields["code_insee"]
            )
            erp_basic_fields["code_postal"] = self._handle_5digits_code(
                erp_basic_fields, erp_basic_fields["postal_code"]
            )
            return erp_basic_fields
        except KeyError as key:
            raise RuntimeError(
                f"Impossible d'extraire des données: champ {key} manquant"
            )
        except Activite.DoesNotExist:
            raise Exception(f"{erp_basic_fields['activite']}")

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

    def _get_typed_value(self, key, value):
        if get_type(key) == "boolean":
            if get_nullable(key) is True:
                if not value:
                    return None
            return True if value in ["True", "true"] else False
        elif get_type(key) == "string":
            return value
        elif get_type(key) == "number":
            if get_nullable(key) is True:
                if not value:
                    return None
            try:
                return int(value)
            except ValueError:
                return None
        elif get_type(key) == "array":
            if get_nullable(key) is True:
                if not value:
                    return None
            try:
                return value.split(",")
            except ValueError:
                return None

    def _build_a11y(self, erp, data):
        accessibility_fields = {
            k: self._get_typed_value(k, v)
            for k, v in data.items()
            if k in self.accessibility_fields
        }
        return Accessibilite(erp=erp, **accessibility_fields)

    def _populate_accessibilite(
        self,
    ):
        if not self.erp.has_accessibilite():
            accessibilite = self._build_a11y(erp=self.erp, data=self.record)
            accessibilite.save()
            self.erp.accessibilite = accessibilite
            self.erp.save()
