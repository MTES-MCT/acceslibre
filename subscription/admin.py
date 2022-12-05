from django.contrib import admin
from django.utils.safestring import mark_safe

from subscription.models import ErpSubscription


@admin.register(ErpSubscription)
class ErpSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "get_erp",
        "user",
        "created_at",
        "updated_at",
    )
    list_filter = [
        "created_at",
    ]
    # list_display_links = ("created_at",)
    list_select_related = ("erp", "erp__activite", "user")
    ordering = ("-created_at",)
    search_fields = ("erp__nom", "user__username")
    autocomplete_fields = ["erp", "user"]

    def get_erp(self, obj):
        if obj.erp:
            return mark_safe(f'<a href="{obj.erp.get_absolute_url()}" target="_blank">{obj.erp}</a>')
        return ""

    get_erp.short_description = "ERP"
