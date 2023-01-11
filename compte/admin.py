from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Count, Q
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
        "get_erp_count_published",
        "get_erp_count_total",
        "get_vote_count",
    )
    list_per_page = 20

    def get_erp_count_published(self, obj):
        return obj.erp_count_published

    get_erp_count_published.short_description = "Pub. ERP"
    get_erp_count_published.admin_order_field = "erp_count_published"

    def get_erp_count_total(self, obj):
        return obj.erp_count_total

    get_erp_count_total.short_description = "Tot. ERP"
    get_erp_count_total.admin_order_field = "erp_count_total"

    def get_vote_count(self, obj):
        return obj.vote_count

    get_vote_count.short_description = "Votes"
    get_vote_count.admin_order_field = "vote_count"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(vote_count=Count("vote", distinct=True))
            .annotate(erp_count_total=Count("erp", distinct=True))
            .annotate(erp_count_published=Count("erp", filter=Q(erp__published=True), distinct=True))
        )


# Replace the default UserAdmin with our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserPreferences)
