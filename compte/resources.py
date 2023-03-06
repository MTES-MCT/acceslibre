from django.contrib.auth.models import User
from import_export import resources
from import_export.fields import Field

from compte.models import UserStats


class UserAdminResource(resources.ModelResource):
    vote_count = Field()
    nb_erp_created = Field()
    nb_erp_edited = Field()
    nb_erp_attributed = Field()

    class Meta:
        model = User
        skip_unchanged = True
        fields = [
            "username",
            "email",
            "date_joined",
            "last_login",
            "is_active",
            "is_staff",
        ]
        export_order = fields + ["vote_count", "nb_erp_created", "nb_erp_edited", "nb_erp_attributed"]

    def dehydrate_vote_count(self, user):
        return user.vote_count

    def dehydrate_nb_erp_created(self, user):
        try:
            return user.stats.nb_erp_created
        except UserStats.DoesNotExist:
            return "N/A"

    def dehydrate_nb_erp_edited(self, user):
        try:
            return user.stats.nb_erp_edited
        except UserStats.DoesNotExist:
            return "N/A"

    def dehydrate_nb_erp_attributed(self, user):
        try:
            return user.stats.nb_erp_attributed
        except UserStats.DoesNotExist:
            return "N/A"
