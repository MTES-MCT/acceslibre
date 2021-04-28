from django.core.management import BaseCommand

from erp.export.create_schema import generate_schema


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            generate_schema(
                base="erp/export/base-schema.json", outfile="erp/export/schema.json"
            )
        except KeyboardInterrupt:
            print("Interrompu.")
