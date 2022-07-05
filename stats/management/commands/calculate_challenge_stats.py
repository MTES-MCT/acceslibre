from django.core.management import BaseCommand, CommandError

from stats.models import Challenge


class Command(BaseCommand):
    help = "Calcule les statistiques concernant les challenges en cours"

    def handle(self, *args, **options):
        for challenge in Challenge.objects.filter(active=True):
            try:
                challenge.refresh_stats()
                print(f"STATS for challenge {challenge} update successfully")
            except KeyboardInterrupt:
                raise CommandError("Interrompu.")
