import csv

import reversion
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

from erp import schema
from erp.imports.serializers import ErpImportSerializer
from erp.models import Accessibilite, Erp, ExternalSource

TRUE_VALUES = {"1", "true", "vrai", "oui", "o", "yes", "y", "t"}
FALSE_VALUES = {"0", "false", "faux", "non", "none", "n", "no", "f"}

SOURCE_FIELDS = {
    "stationnement_ext_presence": ("stationnement_ext_pmr",),
    "cheminement_ext_presence": ("cheminement_ext_plain_pied", "cheminement_ext_bande_guidage"),
    "entree_porte_presence": ("entree_porte_type",),
    "entree_dispositif_appel": ("entree_dispositif_appel_type",),
    "entree_aide_humaine": ("accueil_personnels",),
    "sanitaires_presence": ("sanitaires_adaptes",),
}

INVERSE_CHILDREN_CONSTRAINTS = (
    "entree_plain_pied",
    "cheminement_ext_plain_pied",
    "accueil_cheminement_plain_pied",
)


class Command(BaseCommand):
    help = (
        "Importe les établissements Doctolib (fichier doctolib.csv). "
        "Complète les ERP déjà rapprochés ou crée les nouveaux, et enregistre "
        "les identifiants Doctolib et RPPS dans les sources."
    )

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, default="doctolib.csv", help="Chemin du fichier CSV à traiter")
        parser.add_argument("--dry-run", action="store_true", help="Valide les lignes sans les enregistrer")
        parser.add_argument("--verbose", action="store_true", help="Affiche le détail des erreurs")

    @staticmethod
    def _clean(value):
        return (value or "").strip()

    @classmethod
    def _boolean(cls, value):
        value = cls._clean(value).lower()
        if value in TRUE_VALUES:
            return True
        if value in FALSE_VALUES:
            return False
        return None

    @classmethod
    def _sources(cls, record):
        sources = []
        doctolib_id = cls._clean(record.get("id docto"))
        rpps = cls._clean(record.get("rpps"))
        if doctolib_id:
            sources.append({"source": ExternalSource.SOURCE_DOCTOLIB, "source_id": doctolib_id})
        if rpps:
            sources.append({"source": ExternalSource.SOURCE_ANNUAIRE_SANTE, "source_id": rpps})
        return sources

    @classmethod
    def _accessibilite(cls, record):
        data = {}

        parking = cls._boolean(record.get("wheelchair_route.has_accessible_parking_nearby"))
        if parking is not None:
            data["stationnement_ext_presence"] = parking
            if parking is True:
                data["stationnement_ext_pmr"] = True

        accessible_path = cls._boolean(record.get("wheelchair_route.has_accessible_path_to_entrance"))
        guiding_strips = cls._boolean(record.get("equipment.has_floor_guiding_strips"))
        if accessible_path is not None or guiding_strips is not None:
            data["cheminement_ext_presence"] = True
        if accessible_path is not None:
            data["cheminement_ext_plain_pied"] = accessible_path
        if guiding_strips is not None:
            data["cheminement_ext_bande_guidage"] = guiding_strips

        automatic_doors = cls._boolean(record.get("wheelchair_route.has_automatic_doors"))
        if automatic_doors is not None:
            data["entree_porte_presence"] = True
            data["entree_porte_type"] = schema.PORTE_TYPE_AUTOMATIQUE if automatic_doors else schema.PORTE_TYPE_MANUELLE

        step_free = cls._boolean(record.get("wheelchair_route.has_step_free_access"))
        if step_free is not None:
            data["entree_plain_pied"] = step_free
            data["accueil_cheminement_plain_pied"] = step_free

        elevator = cls._boolean(record.get("elevator.present"))
        elevator_pmr = cls._boolean(record.get("elevator.has_min_width"))
        if step_free is not True:
            if elevator is not None:
                data["accueil_cheminement_ascenseur"] = elevator
                if elevator is True and elevator_pmr is not None:
                    data["accueil_cheminement_ascenseur_pmr"] = elevator_pmr
            elif elevator_pmr is True:
                data["accueil_cheminement_ascenseur"] = True
                data["accueil_cheminement_ascenseur_pmr"] = True

        handrail = cls._clean(record.get("stairs.handrail"))
        if handrail and step_free is not True:
            data["accueil_cheminement_main_courante"] = handrail.lower() not in FALSE_VALUES

        intercom = cls._boolean(record.get("intercom.present"))
        if intercom is not None:
            data["entree_dispositif_appel"] = intercom
            if intercom is True:
                data["entree_dispositif_appel_type"] = [schema.DISPOSITIFS_APPEL_INTERPHONE]

        staff_assistance = cls._boolean(record.get("patient_reception.has_staff_assistance"))
        if staff_assistance is not None:
            data["entree_aide_humaine"] = staff_assistance
            if staff_assistance is True:
                data["accueil_personnels"] = schema.PERSONNELS_FORMES

        min_width = cls._boolean(record.get("wheelchair_route.has_min_width"))
        if min_width is True:
            data["entree_largeur_mini"] = 80
            data["accueil_retrecissement"] = False

        accessible_restroom = cls._boolean(record.get("equipment.has_accessible_restroom"))
        if accessible_restroom is not None:
            data["sanitaires_presence"] = accessible_restroom
            if accessible_restroom is True:
                data["sanitaires_adaptes"] = True

        provider_experience = cls._boolean(record.get("patient_reception.has_provider_disability_experience"))
        if provider_experience is not None:
            data["accueil_soignant"] = provider_experience

        return data

    @staticmethod
    def _is_empty(value):
        return value is None or value == "" or value == [] or value == ()

    @staticmethod
    def _children(field):
        return schema.FIELDS.get(field, {}).get("children", [])

    @classmethod
    def _any_existing_children(cls, erp, field):
        return any(not cls._is_empty(getattr(erp.accessibilite, child, None)) for child in cls._children(field))

    @classmethod
    def _filter_existing_accessibility(cls, data, erp):
        if erp is None or not erp.has_accessibilite():
            return data

        filtered = {key: value for key, value in data.items() if cls._is_empty(getattr(erp.accessibilite, key, None))}

        for parent in SOURCE_FIELDS:
            if filtered.get(parent) is False and cls._any_existing_children(erp, parent):
                filtered.pop(parent)

        for parent in INVERSE_CHILDREN_CONSTRAINTS:
            if filtered.get(parent) is True and cls._any_existing_children(erp, parent):
                filtered.pop(parent)

        def final(field):
            return filtered[field] if field in filtered else getattr(erp.accessibilite, field, None)

        if final("accueil_cheminement_plain_pied") is True:
            for child in cls._children("accueil_cheminement_plain_pied"):
                filtered.pop(child, None)

        for parent, children in SOURCE_FIELDS.items():
            if final(parent) is not True:
                for child in children:
                    filtered.pop(child, None)

        if final("accueil_cheminement_ascenseur") is not True:
            filtered.pop("accueil_cheminement_ascenseur_pmr", None)

        return filtered

    @classmethod
    def _existing_accessibility(cls, erp):
        if erp is None or not erp.has_accessibilite():
            return {}

        existing = {}
        for field in Accessibilite._meta.concrete_fields:
            if field.name in ("id", "erp"):
                continue
            value = getattr(erp.accessibilite, field.name, None)
            if not cls._is_empty(value):
                existing[field.name] = value
        return existing

    @classmethod
    def _build_data(cls, record, erp, accessibility=None):
        doctolib_id = cls._clean(record.get("id docto"))
        if accessibility is None:
            accessibility = cls._filter_existing_accessibility(cls._accessibilite(record), erp)
        accessibility = cls._existing_accessibility(erp) | accessibility

        data = {
            "nom": erp.nom if erp else cls._clean(record.get("Nom")),
            "commune": erp.commune if erp else cls._clean(record.get("commune")),
            "code_postal": erp.code_postal if erp else cls._clean(record.get("code_postal")),
            "numero": erp.numero if erp else cls._clean(record.get("numero")),
            "voie": erp.voie if erp else cls._clean(record.get("voie")),
            "lieu_dit": erp.lieu_dit if erp else None,
            "code_insee": erp.code_insee if erp else None,
            "activite": erp.activite.nom if erp and erp.activite else cls._clean(record.get("Activité corrigée")),
            "sources": cls._sources(record),
            "accessibilite": accessibility,
        }

        if erp is None:
            data["source"] = ExternalSource.SOURCE_DOCTOLIB
            data["source_id"] = doctolib_id
            latitude = cls._clean(record.get("latitude"))
            longitude = cls._clean(record.get("longitude"))
            if latitude and longitude:
                try:
                    data["latitude"] = float(latitude)
                    data["longitude"] = float(longitude)
                except ValueError:
                    pass

        return data

    def _find_existing_erp(self, record):
        accesslibre_id = self._clean(record.get("id acceslibre final sans"))
        if accesslibre_id:
            try:
                pk = int(accesslibre_id)
            except ValueError:
                return None, f"identifiant AccesLibre invalide : {accesslibre_id!r}"
            erp = Erp.objects.filter(pk=pk).first()
            if not erp:
                return None, f"aucun ERP avec l'identifiant AccesLibre {pk}"
            return erp, None

        doctolib_id = self._clean(record.get("id docto"))
        if doctolib_id:
            erp = Erp.objects.filter(
                sources__source=ExternalSource.SOURCE_DOCTOLIB,
                sources__source_id=doctolib_id,
            ).first()
            if erp:
                return erp, None

        return None, None

    @staticmethod
    def _update_sources(erp, sources):
        for source_data in sources:
            ExternalSource.objects.filter(erp=erp, source=source_data["source"]).delete()
            ExternalSource.objects.create(erp_id=erp.pk, **source_data)

    def _save(self, serializer):
        with reversion.create_revision():
            erp = serializer.save()
            reversion.set_comment("Import Doctolib")
        return erp

    def handle(self, *args, **options):
        input_file = options["file"]
        dry_run = options["dry_run"]
        verbose = options["verbose"]

        try:
            with open(input_file, encoding="utf-8-sig", newline="") as file:
                records = list(csv.DictReader(file, delimiter=","))
        except FileNotFoundError:
            raise CommandError(f"Le fichier {input_file} est introuvable.")

        results = {
            "created": 0,
            "updated": 0,
            "skipped_no_name": 0,
            "skipped_no_erp": 0,
            "duplicated": 0,
            "in_error": 0,
        }

        for line_number, record in enumerate(records, start=1):
            accesslibre_id = self._clean(record.get("id acceslibre final sans"))
            name = self._clean(record.get("Nom"))

            if not accesslibre_id and not name:
                results["skipped_no_name"] += 1
                continue

            erp, error = self._find_existing_erp(record)
            if error:
                results["skipped_no_erp"] += 1
                if verbose:
                    self.stderr.write(f"Ligne {line_number} ignorée : {error}")
                continue

            is_update = erp is not None
            if is_update and not erp.has_accessibilite() and not dry_run:
                erp.accessibilite = Accessibilite.objects.create(erp=erp)

            accessibility = self._filter_existing_accessibility(self._accessibilite(record), erp)

            if is_update and not accessibility:
                if not dry_run:
                    with reversion.create_revision():
                        self._update_sources(erp, self._sources(record))
                        reversion.set_comment("Import Doctolib")
                results["updated"] += 1
                continue

            data = self._build_data(record, erp, accessibility)

            serializer = ErpImportSerializer(
                instance=erp,
                data=data,
                context={"enrich_only": is_update},
            )

            try:
                serializer.is_valid(raise_exception=True)
                if not dry_run:
                    erp = self._save(serializer)
            except ValidationError as exc:
                if "non_field_errors" in exc.get_codes() and "duplicate" in exc.get_codes()["non_field_errors"]:
                    results["duplicated"] += 1
                else:
                    results["in_error"] += 1
                if verbose:
                    self.stderr.write(f"Ligne {line_number} : {exc}")
                continue
            except IntegrityError as exc:
                results["in_error"] += 1
                if verbose:
                    self.stderr.write(f"Ligne {line_number} : {exc}")
                continue

            results["updated" if is_update else "created"] += 1

        self.stdout.write(
            "Import Doctolib terminé :\n"
            f"  - Créés : {results['created']}\n"
            f"  - Mis à jour : {results['updated']}\n"
            f"  - Ignorés (nom vide) : {results['skipped_no_name']}\n"
            f"  - Ignorés (ERP introuvable) : {results['skipped_no_erp']}\n"
            f"  - Doublons : {results['duplicated']}\n"
            f"  - Erreurs : {results['in_error']}"
        )
