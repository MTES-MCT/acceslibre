import json
import requests

from django.core.management.base import BaseCommand

from core.lib import geo
from erp.models import Commune, Erp

# Standard (Polygon)
# https://geo.api.gouv.fr/communes/34120?fields=contour&format=json&geometry=contour
# Commune "trouée" (MultiPolygon)
# https://geo.api.gouv.fr/communes/2B049?fields=contour&format=json&geometry=contour

TYPE_UPDATED = "updated"
TYPE_ERROR = "errors"
TYPE_MISSING_DELETED = "missing"
TYPE_MISSING_WITH_ERPS = "missing-erps"


class NotFound(Exception):
    pass


class Undecodable(Exception):
    pass


class Command(BaseCommand):
    report = {
        TYPE_UPDATED: [],
        TYPE_ERROR: [],
        TYPE_MISSING_DELETED: [],
        TYPE_MISSING_WITH_ERPS: [],
    }

    def handle(self, *args, **options):
        try:
            self.process()
        except KeyboardInterrupt:
            print("\nInterrupted")
        finally:
            self.print_report()

    def process(self):
        for commune in Commune.objects.filter(
            arrondissement=False,  # we already have contours for arrondissements
            contour__isnull=True,
        ):
            try:
                raw_contour = self.get_contour(commune.code_insee)
            except NotFound:
                base_msg = f"{commune.nom} ({commune.code_insee}) not found"
                # check for existing Erp with this code
                count = Erp.objects.filter(commune_ext=commune).count()
                if count > 0:
                    self.log(
                        TYPE_MISSING_WITH_ERPS, f"{count} erps attached to {base_msg}"
                    )
                else:
                    commune.delete()
                    self.log(TYPE_MISSING_DELETED, f"{base_msg}, deleted")
                continue
            except (Undecodable, requests.RequestException) as err:
                self.log(TYPE_ERROR, f"Request error or undecodable JSON: {err}")
            try:
                commune.contour = geo.geojson_mpoly(raw_contour)
                commune.save()
                self.log(
                    TYPE_UPDATED,
                    f"Updated contour for {commune.nom} ({commune.code_insee})",
                )
            except TypeError as err:
                self.log(
                    TYPE_ERROR,
                    f"Unable to store contour for {commune.nom} ({commune.code_insee}): {err}",
                )

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

    def log(self, type, data):
        if type == TYPE_UPDATED:
            self.report[TYPE_UPDATED].append(data)
            self.log_char("U")
        elif type == TYPE_ERROR:
            self.report[TYPE_ERROR].append(data)
            self.log_char("E")
        elif type == TYPE_MISSING_DELETED:
            self.report[TYPE_MISSING_DELETED].append(data)
            self.log_char("X")
        elif type == TYPE_MISSING_WITH_ERPS:
            self.report[TYPE_MISSING_WITH_ERPS].append(data)
            self.log_char("!")

    def log_char(self, char):
        print(char, end="", flush=True)

    def print_report(self):
        self.print_report_section("Non-existent", self.report[TYPE_MISSING_DELETED])
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
