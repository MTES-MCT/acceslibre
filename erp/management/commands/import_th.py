import csv
import os
import re
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from rest_framework.exceptions import ValidationError

from erp.imports.mapper.base import BaseMapper
from erp.imports.serializers import ErpImportSerializer
from erp.models import Activite, Erp

VALEURS_VIDES = ["-", "https://", "http://"]


def clean(string):
    if string in VALEURS_VIDES:
        return ""
    return str(string).replace("\n", " ").replace("«", "").replace("»", "").replace("’", "'").replace('"', "").strip()


def clean_activity(string):
    if string in VALEURS_VIDES:
        return ""
    return str(string).replace("\n", " ").replace("«", "").replace("»", "").replace('"', "").strip()


def clean_website(url):
    if url.endswith(";"):
        url = url[:-1]
    if url.startswith("www."):
        return f"http://{url}"


class Command(BaseCommand):
    help = "Importe les données Tourisme & Handicap"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Chemin du fichier à traiter",
        )

    def get_familles(self, entry: dict):
        if not entry:
            return None

        handicaps = {
            "auditif": True if str(entry.get("auditif")) == "1" else False,
            "mental": True if str(entry.get("mental")) == "1" else False,
            "moteur": True if str(entry.get("moteur")) == "1" else False,
            "visuel": True if str(entry.get("visuel")) == "1" else False,
        }
        return [k for k, v in handicaps.items() if v is True]

    def get_or_create_erp(self, entry: dict):
        entry["activite"] = Activite.objects.get(nom=clean_activity(entry.get("activite")))
        entry["commune"] = entry["ville"]
        entry["code_postal"] = BaseMapper.handle_5digits_code(entry["code_postal"])

        existing = Erp.objects.find_duplicate(
            numero=clean(entry.get("numero")),
            commune=clean(entry.get("ville")),
            activite=entry["activite"],
            voie=clean(entry.get("voie")),
            lieu_dit=clean(entry.get("lieu_dit")),
        ).first()

        if existing:
            return existing

        entry["site_internet"] = clean_website(entry["site_internet"])

        entry["accessibilite"] = {"entree_porte_presence": True}
        serializer = ErpImportSerializer(data=entry)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as err:
            if "duplicate" in err.get_codes().get("non_field_errors", []):
                existing = Erp.objects.get(
                    pk=re.search(
                        r".*ERP #(\d*)",
                        err.detail["non_field_errors"][0].__str__(),
                    ).group(1)
                )
                serializer = ErpImportSerializer(instance=existing, data=entry)
                serializer.is_valid(raise_exception=True)
            else:
                raise err
        return serializer.save()

    def handle(self, *args, **options):
        self.input_file = options.get("file")
        # make a backup of previously flagged T&H
        csv_old_th_filename = f"old_th_{datetime.now().strftime('%Y-%m-%d_%Hh%Mm%S')}.csv"
        with open(os.path.join(settings.BASE_DIR, csv_old_th_filename), "w") as csvfile:
            fieldnames = ["ID", "labels", "labels_familles_handicap"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for erp in Erp.objects.filter(accessibilite__labels__contains=["th"]):
                writer.writerow(
                    {
                        "ID": erp.pk,
                        "labels": erp.accessibilite.labels,
                        "labels_familles_handicap": erp.accessibilite.labels_familles_handicap,
                    }
                )

        # create or update
        errors = []
        erps = []
        with open(self.input_file, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for i, row in enumerate(reader):
                print(f"~ Processing line {i}")
                try:
                    erp = self.get_or_create_erp(row)
                except Activite.DoesNotExist:
                    row["error"] = "Activité non trouvée"
                    errors.append(row)
                    print(f"### Activite not found with name {row['activite']} - line {i+2}")
                    continue
                except ValidationError as err:
                    row["error"] = str(err)
                    errors.append(row)
                    print(f"### Validation error while processing {row['nom']}: {err}")
                    continue

                if not erp:
                    print(f"### Cannot insert {row['nom']} in DB.")
                    continue
                erps.append(erp.pk)
                access = erp.accessibilite
                access.labels_familles_handicap = self.get_familles(row)
                access.labels = access.labels or []
                if "th" not in access.labels:
                    access.labels.append("th")
                access.save()
                print(f"### Done for {row['nom']}: {access.labels_familles_handicap}")

        if errors:
            csv_error_th_filename = f"error_th_{datetime.now().strftime('%Y-%m-%d_%Hh%Mm%S')}.csv"
            with open(os.path.join(settings.BASE_DIR, csv_error_th_filename), "w") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=errors[0].keys())
                writer.writeheader()
                for error in errors:
                    writer.writerow(error)

        # remove 'th' from labels & remove familles handicap
        to_remove = Erp.objects.filter(accessibilite__labels__contains=["th"]).exclude(pk__in=erps)
        for erp in to_remove:
            access = erp.accessibilite
            access.labels.remove("th")
            access.labels_familles_handicap = []
            access.save()
            print(f"ERP#{erp.pk} has no TH labels anymore nor families")
