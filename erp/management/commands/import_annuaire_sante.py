"""
This management command is in charge of formatting the annuaire-sante.csv into a compatible version to use the
validate_and_import_file management command.
"""

import csv

from django.core.management.base import BaseCommand

from erp.imports.mapper.base import BaseMapper
from erp.provider.geocoder import geocode
from erp.models import ExternalSource


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="File to process (CSV separated by ;)",
        )

    def handle(self, *args, **options):  # noqa
        input_file = options.get("file")
        output_file = "formatted_" + input_file

        with open(input_file, mode="r", encoding="utf-8") as infile:
            reader = csv.DictReader(infile, delimiter=";")
            fieldnames = reader.fieldnames + [
                "numero",
                "voie",
                "lieu_dit",
                "code_postal",
                "commune",
                "code_insee",
                "source",
            ]
            rows = list(reader)

        with open(output_file, mode="w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                row["postal_code"] = BaseMapper.handle_5digits_code(row["postal_code"].strip())
                try:
                    geo = geocode(row["voie"], row["postal_code"])
                except RuntimeError:
                    print(f"Cannot geocode {row['voie']} {row['postal_code']}")
                    continue
                if not geo:
                    print(f"Cannot geocode {row['voie']} {row['postal_code']}")
                    continue
                for attr in ("numero", "voie", "lieu_dit", "code_postal", "commune", "code_insee"):
                    row[attr] = geo.get(attr, "")
                row["source"] = ExternalSource.SOURCE_ANNUAIRE_SANTE
                writer.writerow(row)

        print(f"File successfully written to {output_file} can now use the validate_and_import_file management command")

        print("You can now use the following command to import the file:")
        print(f"python manage.py validate_and_import_file --force_update --file {output_file}")
