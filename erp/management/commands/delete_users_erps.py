from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from erp.models import Erp


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("username", help="Adresse email de la personne")
        parser.add_argument(
            "--write",
            action="store_true",
            help="Actually edit the database",
        )

    def _delete_erps(self, user):
        erps = Erp.objects.filter(user=user).exclude(checked_up_to_date_at__isnull=False)
        print(f"Found {erps.count()} erp for user {user}")
        deleted = 0

        for erp in erps:
            revisions = erp.get_history(exclude_changes_from=user)
            user_is_only_editor = len(revisions) == 0
            if user_is_only_editor:
                print(f"Will delete {erp}")
                if self.should_write:
                    erp.delete()
                    deleted += 1

        print(f"Deleted {deleted} erps from the database")

    def handle(self, *args, **options):
        self.should_write = options["write"]
        username = options["username"]
        try:
            user = User.objects.get(username__icontains=username)
        except User.DoesNotExist:
            self.stderr.write(f"User with username {username} not found")
            return
        self._delete_erps(user)
