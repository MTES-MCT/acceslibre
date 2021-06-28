import json
import requests

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from progress import bar

from core.lib import geo
from erp.models import Commune, Erp


# Standard (Polygon)
# https://geo.api.gouv.fr/communes/34120?fields=contour&format=json&geometry=contour
# Commune "trouée" (MultiPolygon)
# https://geo.api.gouv.fr/communes/2B049?fields=contour&format=json&geometry=contour


TYPE_ERROR = "errors"
TYPE_OBSOLETE = "obsolete"
TYPE_OBSOLETE_NONEMPTY = "obsolete-nonempty"
TYPE_UPDATED = "updated"


class NotFound(Exception):
    pass


class Undecodable(Exception):
    pass


class Conan(bar.Bar):
    suffix = "%(remaining_minutes)d minutes remaining"

    @property
    def remaining_minutes(self):
        return self.eta // 60


class Command(BaseCommand):
    commune_content_type = ContentType.objects.get_for_model(Commune)
    report = {
        TYPE_ERROR: [],
        TYPE_OBSOLETE: [],
        TYPE_OBSOLETE_NONEMPTY: [],
        TYPE_UPDATED: [],
    }

    def handle(self, *args, **options):
        try:
            self.process()
        except KeyboardInterrupt:
            print("\nInterrupted")
        finally:
            self.print_report()

    def process(self):
        communes = Commune.objects.filter(
            # Note: we already have contours for arrondissements, and the contours
            # provided for them by the API are the ones from the surrounding commune…
            arrondissement=False,
            obsolete=False,
            contour__isnull=True,
        )
        for commune in Conan("Processing").iter(communes):
            try:
                raw_contour = self.get_contour(commune.code_insee)
                commune.contour = geo.geojson_mpoly(raw_contour)
                commune.save()
                self.log(commune, TYPE_UPDATED, "Updated contour OK")
            except NotFound:
                # check for existing Erps attached to this obsolete commune
                count = Erp.objects.filter(commune_ext=commune).count()
                if count > 0:
                    self.log(
                        commune,
                        TYPE_OBSOLETE_NONEMPTY,
                        f"is obsolete with {count} erps",
                    )
                else:
                    commune.obsolete = True
                    commune.save()
                    self.log(commune, TYPE_OBSOLETE, "marked as obsolete")
            except (Undecodable, requests.RequestException) as err:
                self.log(commune, TYPE_ERROR, f"Undecodable/bogus request: {err}")
            except TypeError as err:
                self.log(commune, TYPE_ERROR, f"Failed saving contour: {err}")
            except Exception as err:
                raise CommandError(err)

    def get_contour(self, code_insee):
        try:
            res = requests.get(
                f"https://geo.api.gouv.fr/communes/{code_insee}?fields=contour&format=json"
            )
            res.raise_for_status()
            return res.json()["contour"]
        except (KeyError, json.JSONDecodeError):
            raise Undecodable(code_insee)
        except requests.RequestException as err:
            if err.response.status_code == 404:
                raise NotFound(code_insee)
            else:
                raise err

    def log(self, commune, type_, msg):
        self.report[type_].append(f"{commune.nom} ({commune.code_insee}): {msg}")

    def print_report(self):
        self.print_report_section("Non-existent", self.report[TYPE_OBSOLETE])
        self.print_report_section(
            "Non-existent with ERPs attached", self.report[TYPE_OBSOLETE_NONEMPTY]
        )
        self.print_report_section("Errors", self.report[TYPE_ERROR])
        print("\nDone.")

    def print_report_section(self, title, section):
        print(f"\n{title} ({len(section)} entries):\n")
        if len(section) > 0:
            [print(f"- {msg}") for msg in section]
        else:
            print("No entries")
