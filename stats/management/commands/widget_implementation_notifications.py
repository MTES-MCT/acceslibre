from django.core.management import BaseCommand, CommandError

from stats.models import Referer


class Command(BaseCommand):
    help = "Send notifications for widget implementation."

    def handle(self, *args, **options):
        for referer in Referer.objects.filter(
            date_notification_to_mattermost__isnull=True
        ):
            try:
                referer.notif_mattermost()
            except KeyboardInterrupt:
                raise CommandError("Interrompu.")
            else:
                print(f"NOTIF for referer {referer} sended")
