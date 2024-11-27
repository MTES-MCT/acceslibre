from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Q
from reversion.models import Version

from erp.models import Accessibilite, Erp
from django.db.utils import IntegrityError
from reversion.errors import RevertError


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("email")
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

        for erp in erps:
            versions = Version.objects.filter(
                Q(object_id=erp.pk, content_type=erp_content_type)
                | Q(object_id=erp.accessibilite.pk, content_type=access_content_type)
            )
            if not versions:
                continue

            last_entry = versions.first()
            if last_entry.revision.user != user:
                continue

            if erp.checked_up_to_date_at and last_entry.revision.date_created < erp.checked_up_to_date_at:
                continue

            version_to_revert_to = None
            for version in versions:
                if version.revision.user != user:
                    version_to_revert_to = version
                    break

            if not version_to_revert_to:
                if self.should_write:
                    print(f"Deleting ERP {erp} with no other changes...")
                    erp.delete()
                    print("...Deleted")
                else:
                    print(f"Would have deleted ERP {erp}")
                continue

            if self.should_write:
                print(f"Reverting {version_to_revert_to.revision.__dict__} ...")
                try:
                    version_to_revert_to.revision.revert()
                except IntegrityError:
                    print("... Cannot be reverted due to accessibility inconsistencies.")
                    continue
                except RevertError:
                    print("... Cannot be reverted, old version not valid anymore.")
                    continue
                print("... Reverted.")
            else:
                print(f"Would have reverted {version_to_revert_to.revision}")

    def handle(self, *args, **options):
        self.should_write = options["write"]
        email = options["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stderr.write(f"User with email {email} not found")
            return

        self._revert_changes_on_erp(user)
