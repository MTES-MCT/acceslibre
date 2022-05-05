from django.contrib import admin

from stats.models import Challenge, Referer, Implementation


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("nom", "slug", "start_date", "end_date", "nb_erp_total_added")
    ordering = ("nom",)
    search_fields = ("nom",)


@admin.register(Referer)
class RefererAdmin(admin.ModelAdmin):
    list_display = ("domain",)
    search_fields = ("domain",)


@admin.register(Implementation)
class ImplementationAdmin(admin.ModelAdmin):
    list_display = ("referer", "urlpath", "created_at", "updated_at")
    search_fields = ("referer", "urlpath", "created_at")
