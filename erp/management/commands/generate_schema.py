from django.core.management import BaseCommand, CommandError

from erp.export.generate_schema import generate_schema


class Command(BaseCommand):
    help = "Génère un TableSchema à partir du schema de données"
    default_dir = "erp/export/static"

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-file",
            type=str,
            help=f"Fichier contenant un schema prérempli sans champs. Défaut: {self.default_dir}/base-schema.json",
        )
        parser.add_argument(
            "--out-file",
            type=str,
            help=f"Destination du fichier généré. Défaut: {self.default_dir}/schema.json",
        )

    def handle(self, *args, **options):
        base = options.get("base-file", self.default_dir + "/base-schema.json")
        outfile = options.get("out-file", self.default_dir + "/schema.json")
        repository = "https://github.com/MTES-MCT/acceslibre-schema/raw/v0.0.19/"
        try:
            generate_schema(base=base, outfile=outfile, repository=repository)
            print(f"Schema generated to: {outfile}")

        except KeyboardInterrupt:
            raise CommandError("Interrompu.")
