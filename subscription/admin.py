from django.contrib import admin
from django.utils.html import escape, format_html

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
            return format_html('<a href="{}" target="_blank">{}</a>', obj.erp.get_absolute_url(), escape(obj.erp))
        return ""

    get_erp.short_description = "ERP"
