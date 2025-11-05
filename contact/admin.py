from django.contrib import admin
from django.db import models
from django.utils.html import escape, format_html
from django_summernote.widgets import SummernoteWidget
from modeltranslation.admin import TranslationAdmin

from .models import FAQ, Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "topic",
        "get_erp",
        "name",
        "email",
        "user",
        "sent_ok",
    )
    list_filter = [
        "topic",
        "sent_ok",
        "created_at",
    ]
    list_display_links = ("created_at",)
    list_select_related = ("erp", "erp__activite", "erp__commune_ext", "user")
    ordering = ("-created_at",)
    search_fields = ("name", "topic", "user__username", "email", "erp__nom")
    autocomplete_fields = ["erp", "user"]
    readonly_fields = [
        "created_at",
        "user",
        "name",
        "email",
        "topic",
        "erp",
        "body",
        "sent_ok",
    ]

    def get_erp(self, obj):
        if obj.erp:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.erp.get_absolute_url(), escape(obj.erp))
        return ""

    get_erp.short_description = "ERP"


@admin.register(FAQ)
class FAQAdmin(TranslationAdmin):
    formfield_overrides = {
        models.TextField: {"widget": SummernoteWidget},
    }
