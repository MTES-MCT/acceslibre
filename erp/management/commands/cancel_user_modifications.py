from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from reversion.models import Version

from erp import schema
from erp.models import Accessibilite, Erp


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument(
            "--write",
            action="store_true",
            help="Actually edit the database",
        )

    def _find_previous_value(self, change):
        choices = schema.get_field_choices(change["field"])
        if not choices:
            return change["old"]

        for possible_value, _ in choices:
            if schema.get_human_readable_value(change["field"], possible_value) == change["old"]:
                return possible_value

    def _get_actual_value(self, change, erp):
        try:
            actual_value = getattr(erp, change["field"])
        except AttributeError:
            actual_value = getattr(erp.accessibilite, change["field"])

        return schema.get_human_readable_value(change["field"], actual_value)

    def _revert_changes_on_erp(self, user):
        erp_content_type = ContentType.objects.get_for_model(Erp)
        erp_versions_by_user = Version.objects.filter(revision__user=user, content_type=erp_content_type)
        erp_ids = list(erp_versions_by_user.values_list("object_id", flat=True))
        erp_edited_by_user = Erp.objects.filter(id__in=erp_ids)
        print("ERP edited by user")
        print(erp_edited_by_user.count())

        access_content_type = ContentType.objects.get_for_model(Accessibilite)
        access_versions_by_user = Version.objects.filter(revision__user=user, content_type=access_content_type)
        access_ids = list(access_versions_by_user.values_list("object_id", flat=True))
        erp_access_edited_by_user = Erp.objects.filter(accessibilite__id__in=access_ids)
        print("ERP (via access) edited by user")
        print(erp_access_edited_by_user.count())

        erps = set(erp_edited_by_user | erp_access_edited_by_user)
        print("Total")
        print(len(erps))

        value_to_change = 0
        for erp in erps:
            history = erp.get_history()
            for log_entry in [h for h in history if h["user"] == user]:
                for change in log_entry["diff"]:
                    users_value = change["new"]
                    actual_value = self._get_actual_value(change, erp)
                    if users_value == actual_value:
                        value_to_change += 1
                        if self.should_write:
                            setattr(erp.accessibilite, change["field"], self._find_previous_value(change))
                            erp.accessibilite.save()
                        else:
                            print(
                                f"Incorrect value for {erp} - {change['field']} is still in place, we should revert or empty this change"
                            )
        print(value_to_change)

    def handle(self, *args, **options):
        self.should_write = options["write"]
        username = options["username"]
        try:
            user = User.objects.get(username__icontains=username)
        except User.DoesNotExist:
            self.stderr.write(f"User with username {username} not found")
            return
        self._revert_changes_on_erp(user)
