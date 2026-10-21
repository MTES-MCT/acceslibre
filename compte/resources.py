from django.contrib.auth.models import User
from import_export import resources
from import_export.fields import Field

from compte.models import UserAPIKey, UserStats


class UserAdminResource(resources.ModelResource):
    nb_erp_created = Field()
    nb_erp_edited = Field()
    nb_erp_attributed = Field()
    nb_erp_administrator = Field()

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
            "nb_erp_created",
            "nb_erp_edited",
            "nb_erp_attributed",
            "nb_erp_administrator",
        ]

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

    def dehydrate_nb_erp_administrator(self, user):
        try:
            return user.stats.nb_erp_administrator
        except UserStats.DoesNotExist:
            return "N/A"

    def dehydrate_nb_erp_attributed(self, user):
        try:
            return user.stats.nb_erp_attributed
        except UserStats.DoesNotExist:
            return "N/A"


class UserAPIKeyResource(resources.ModelResource):
    # Only export non-sensitive data: never `id` (contains the hashed key) nor `hashed_key`.
    username = Field(column_name="Utilisateur")

    class Meta:
        model = UserAPIKey
        fields = (
            "name",
            "prefix",
            "username",
            "description",
            "created",
            "expiry_date",
            "revoked",
        )
        export_order = fields

    def get_queryset(self):
        return super().get_queryset().select_related("user")

    def dehydrate_username(self, obj):
        return obj.user.username if obj.user_id else ""
