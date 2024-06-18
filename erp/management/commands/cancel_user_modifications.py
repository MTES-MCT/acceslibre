from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from reversion.models import Version

from erp.models import Accessibilite, Erp


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument(
            "--write",
            action="store_true",
            help="Actually edit the database",
        )

    def _revert_changes_on_erp(self, user):
        erp_content_type = ContentType.objects.get_for_model(Erp)
        erp_versions_by_user = Version.objects.filter(revision__user=user, content_type=erp_content_type)
        erp_ids = list(erp_versions_by_user.values_list("object_id", flat=True))
        erp_edited_by_user = Erp.objects.filter(id__in=erp_ids)
        print(f"ERP edited by user {erp_edited_by_user.count()}")

        access_content_type = ContentType.objects.get_for_model(Accessibilite)
        access_versions_by_user = Version.objects.filter(revision__user=user, content_type=access_content_type)
        access_ids = list(access_versions_by_user.values_list("object_id", flat=True))
        erp_access_edited_by_user = Erp.objects.filter(accessibilite__id__in=access_ids)
        print(f"ERP (via access) edited by user: {erp_access_edited_by_user.count()}")

        erps = set(erp_edited_by_user | erp_access_edited_by_user)
        print(f"Total number of ERPs with modifications from the user: {len(erps)}")

        to_revert = 0
        for erp in erps:
            history = erp.get_history()
            if not history:
                continue

            last_entry = history[0]
            if last_entry["user"] != user:
                continue

            if erp.checked_up_to_date_at and last_entry["date"] < erp.checked_up_to_date_at:
                continue

            list_of_good_entries = [h for h in history if h["user"] != user]
            if list_of_good_entries:
                to_revert += 1
                if self.should_write:
                    list_of_good_entries[0]["revision"].revert()
                else:
                    print(f"Would have reverted {list_of_good_entries[0]['revision']}")

        print(f"Will have reverted {to_revert} revisions")

    def handle(self, *args, **options):
        self.should_write = options["write"]
        username = options["username"]
        try:
            user = User.objects.get(username__icontains=username)
        except User.DoesNotExist:
            self.stderr.write(f"User with username {username} not found")
            return
        self._revert_changes_on_erp(user)


# TODO change tests
