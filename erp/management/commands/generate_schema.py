from django.core.management import BaseCommand

from erp.export.create_schema import generate_schema


class Command(BaseCommand):
    help = "Génère un TableSchema à partir du schema de données"
    default_dir = "erp/export"

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-file",
            type=str,
            help=f"Fichier contenant un schema prérempli sans champs. Défaut: {self.default_dir}/base-schema.json",
        )
        parser.add_argument(
            "--outfile",
            type=str,
            help=f"Destination du fichier généré. Défaut: {self.default_dir}/schema.json",
        )

    def handle(self, *args, **options):
        base = options.get("base-file", self.default_dir + "/base-schema.json")
        outfile = options.get("outfile", self.default_dir + "/schema.json")
        try:
            generate_schema(base=base, outfile=outfile)
            print(f"Schema generated to: {outfile}")
        except KeyboardInterrupt:
            print("Interrompu.")
