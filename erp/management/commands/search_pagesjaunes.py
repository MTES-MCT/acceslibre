from django.core.management.base import BaseCommand

from erp.provider import pagesjaunes


def format_result(result):
    return f"""- {result["nom"]} (id: {result["source_id"]})
    '{result["numero"]}' '{result["voie"]}'
    {result["code_postal"]} {result["commune"]}
    """


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("what", type=str, help="Activité")
        parser.add_argument("where", type=str, help="Lieu")

    def handle(self, *args, **options):
        try:
            results = pagesjaunes.search(
                what=options.get("what"),
                where=options.get("where"),
            )
            for result in results:
                print(format_result(result))
        except KeyboardInterrupt:
            print("Interrompu.")
