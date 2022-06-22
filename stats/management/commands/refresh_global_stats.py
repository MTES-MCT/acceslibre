from django.core.management import BaseCommand, CommandError

from stats.models import GlobalStats


class Command(BaseCommand):
    help = "Calcule les statistiques globales affichées sur la page Statistiques"

    def handle(self, *args, **options):
        try:
            GlobalStats.objects.get().refresh_stats()
            print("STATS update succesfully")
        except KeyboardInterrupt:
            raise CommandError("Interrompu.")
