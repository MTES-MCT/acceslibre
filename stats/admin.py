from django.contrib import admin

from stats.models import Challenge, ChallengePlayer, ChallengeTeam, WidgetEvent


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("nom", "slug", "start_date", "end_date", "nb_erp_total_added")
    ordering = ("nom",)
    search_fields = ("nom",)
    readonly_fields = ("nb_erp_total_added", "classement", "classement_team")
    exclude = ("created_by",)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ChallengePlayer)
class ChallengePlayerAdmin(admin.ModelAdmin):
    list_display = ("player", "challenge", "inscription_date")
    ordering = ("inscription_date",)
    search_fields = ("player__username", "player__email", "challenge__nom")
    list_filter = ("challenge",)
    autocomplete_fields = ["player"]


admin.site.register(ChallengeTeam)


@admin.register(WidgetEvent)
class WidgetEventAdmin(admin.ModelAdmin):
    list_display = ("domain", "referer_url", "views")
    search_fields = ("urlpath",)
