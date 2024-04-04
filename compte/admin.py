from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from import_export.admin import ExportMixin

from compte.models import UserPreferences
from compte.resources import UserAdminResource


class CustomUserAdmin(ExportMixin, UserAdmin):
    resource_class = UserAdminResource
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

    def get_nb_erp_attributed(self, obj):
        return obj.stats.nb_erp_attributed

    get_nb_erp_attributed.short_description = "Nb ERP attribués"
    get_nb_erp_attributed.admin_order_field = "stats__nb_erp_attributed"


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "notify_on_unpublished_erps",
    )
    search_fields = ("user__email",)


# Replace the default UserAdmin with our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
