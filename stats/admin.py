from django.contrib import admin

from stats.models import Challenge, ChallengePlayer, Referer, Implementation


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("nom", "slug", "start_date", "end_date", "nb_erp_total_added")
    ordering = ("nom",)
    search_fields = ("nom",)
    readonly_fields = ["nb_erp_total_added", "classement"]


@admin.register(ChallengePlayer)
class ChallengePlayerAdmin(admin.ModelAdmin):
    list_display = ("player", "challenge", "inscription_date")
    ordering = ("inscription_date",)
    search_fields = ("player", "challenge")
    list_filter = ("challenge",)


@admin.register(Referer)
class RefererAdmin(admin.ModelAdmin):
    list_display = ("domain", "date_notification_to_mattermost")
    search_fields = ("domain",)
    list_filter = ("date_notification_to_mattermost",)


@admin.register(Implementation)
class ImplementationAdmin(admin.ModelAdmin):
    list_display = ("urlpath", "created_at", "updated_at")
    search_fields = ("referer", "urlpath")
    list_filter = ("referer", "created_at")
