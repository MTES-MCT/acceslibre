import json
import requests

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon


from erp.models import Commune, Erp

# Standard (Polygon)
# https://geo.api.gouv.fr/communes/34120?fields=contour&format=json&geometry=contour
# Commune "trouée" (MultiPolygon)
# https://geo.api.gouv.fr/communes/2B049?fields=contour&format=json&geometry=contour

TYPE_UPDATED = "updated"
TYPE_ERROR = "errors"
TYPE_MISSING = "missing"
TYPE_MISSING_WITH_ERPS = "missing-erps"


class Command(BaseCommand):
    report = {
        TYPE_UPDATED: [],
        TYPE_ERROR: [],
        TYPE_MISSING: [],
        TYPE_MISSING_WITH_ERPS: [],
    }

    def handle(self, *args, **options):
        try:
            for commune in Commune.objects.filter(contour__isnull=True):
                contour_str = get_contour(commune.code_insee)
                if not contour_str:
                    # check for existing Erp with this code
                    count = Erp.objects.filter(commune_ext=commune).count()
                    base_msg = f"non-existent commune {commune.nom} (code {commune.code_insee})"
                    if count > 0:
                        self.log(
                            TYPE_MISSING_WITH_ERPS,
                            f"{count} erps attached to {base_msg}",
                        )
                    else:
                        self.log(
                            TYPE_MISSING,
                            base_msg.title(),
                        )
                    continue
                contour = GEOSGeometry(contour_str)
                try:
                    commune = self.update_commune_contour(commune, contour)
                    self.log(TYPE_UPDATED, f"Updated contour for {commune.nom}")
                except TypeError as err:
                    self.log(TYPE_ERROR, str(err))

        except KeyboardInterrupt:
            print("\nInterrupted")
        finally:
            self.print_report()

    def update_commune_contour(self, commune, contour):
        if isinstance(contour, MultiPolygon):
            pass
        elif isinstance(contour, Polygon):
            contour = MultiPolygon([contour])
        else:
            raise TypeError(f"{contour.contour_type} is not supported")
        commune.contour = contour
        commune.save()
        return commune

    def log(self, type, data):
        if type == TYPE_UPDATED:
            self.report[TYPE_UPDATED].append(data)
            self.log_char("U")
        elif type == TYPE_ERROR:
            self.report[TYPE_ERROR].append(data)
            self.log_char("E")
        elif type == TYPE_MISSING:
            self.report[TYPE_MISSING].append(data)
            self.log_char("X")
        elif type == TYPE_MISSING_WITH_ERPS:
            self.report[TYPE_MISSING_WITH_ERPS].append(data)
            self.log_char("!")

    def log_char(self, char):
        print(char, end="", flush=True)

    def print_report(self):
        self.print_report_section("Non-existent", self.report[TYPE_MISSING])
        self.print_report_section(
            "Non-existent with ERPs attached", self.report[TYPE_MISSING_WITH_ERPS]
        )
        self.print_report_section("Errors", self.report[TYPE_ERROR])
        print("\nDone.")

    def print_report_section(self, title, section):
        print(f"\n{title} ({len(section)} entries):\n")
        if len(section) > 0:
            [print(f"- {msg}") for msg in section]
        else:
            print("No entries")


def get_contour(code_insee):
    try:
        res = requests.get(
            f"https://geo.api.gouv.fr/communes/{code_insee}?fields=contour&format=json&geometry=contour"
        )
        res.raise_for_status()
        return json.dumps(res.json()["contour"])
    except (KeyError, json.JSONDecodeError):
        return
    except requests.RequestException:
        return
