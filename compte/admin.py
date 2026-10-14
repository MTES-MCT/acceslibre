from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from import_export.admin import ExportMixin
from rest_framework_api_key.admin import APIKeyModelAdmin
from rest_framework_api_key.models import APIKey

from compte.models import UserAPIKey, UserPreferences, UserStats
from compte.resources import UserAdminResource, UserAPIKeyResource


class UserStatsInline(admin.StackedInline):
    model = UserStats
    can_delete = False
    verbose_name_plural = "Statistiques"
    fk_name = "user"
    fields = (
        "nb_erp_created",
        "nb_erp_edited",
        "nb_erp_attributed",
        "nb_erp_administrator",
        "nb_profanities",
    )
    readonly_fields = ("nb_erp_created", "nb_erp_edited", "nb_erp_attributed", "nb_erp_administrator")


class CustomUserAdmin(ExportMixin, UserAdmin):
    resource_class = UserAdminResource
    inlines = (UserStatsInline,)

    ordering = (
        "-date_joined",
        "username",
    )
    list_display = (
        "username",
        "email",
        "date_joined",
        "is_active",
        "is_staff",
        "get_nb_erp_created",
        "get_nb_erp_edited",
        "get_nb_erp_attributed",
        "get_nb_erp_administrator",
        "get_nb_profanities",
    )
    list_per_page = 20

    def get_nb_erp_created(self, obj):
        return obj.stats.nb_erp_created

    get_nb_erp_created.short_description = "Nb ERP créés"
    get_nb_erp_created.admin_order_field = "stats__nb_erp_created"

    def get_nb_erp_edited(self, obj):
        return obj.stats.nb_erp_edited

    get_nb_erp_edited.short_description = "Nb ERP édités"
    get_nb_erp_edited.admin_order_field = "stats__nb_erp_edited"

    def get_nb_erp_administrator(self, obj):
        return obj.stats.nb_erp_administrator

    get_nb_erp_administrator.short_description = "Nb ERP gestionnaire"
    get_nb_erp_administrator.admin_order_field = "stats__nb_erp_administrator"

    def get_nb_erp_attributed(self, obj):
        return obj.stats.nb_erp_attributed

    get_nb_erp_attributed.short_description = "Nb ERP attribués"
    get_nb_erp_attributed.admin_order_field = "stats__nb_erp_attributed"

    def get_nb_profanities(self, obj):
        return obj.stats.nb_profanities

    get_nb_profanities.short_description = "Nb de contenus inappropriés"
    get_nb_profanities.admin_order_field = "stats__nb_profanities"


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "notify_on_unpublished_erps",
    )
    search_fields = ("user__email",)


admin.site.unregister(APIKey)


@admin.register(APIKey)
class LegacyAPIKeyAdmin(APIKeyModelAdmin):
    def has_add_permission(self, request):
        return False


@admin.register(UserAPIKey)
class UserAPIKeyAdmin(ExportMixin, APIKeyModelAdmin):
    resource_class = UserAPIKeyResource
    list_display = [*APIKeyModelAdmin.list_display, "user"]
    list_select_related = ("user",)
    search_fields = [*APIKeyModelAdmin.search_fields, "user__username", "user__email", "description"]
    autocomplete_fields = ["user"]
    fields = ("user", "name", "description", "prefix", "revoked", "expiry_date")


# Replace the default UserAdmin with our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
