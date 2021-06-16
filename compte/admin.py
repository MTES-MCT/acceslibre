from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Count

from erp.models import Erp


class CustomUserAdmin(UserAdmin):
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
        "get_rev_count",
    )
    list_per_page = 20

    def get_erp_count_published(self, obj):
        # triggering one Erp count query per user because of performance
        # sometimes many fast sql queries are better than a large & slow one
        return Erp.objects.filter(
            user=obj,
            published=True,
            accessibilite__isnull=False,
            geom__isnull=False,
        ).count()

    get_erp_count_published.short_description = "Pub. ERP"
    get_erp_count_published.admin_order_field = "erp_count_published"

    def get_erp_count_total(self, obj):
        # triggering one Erp count query per user because of performance
        # sometimes many fast sql queries are better than a large & slow one
        return Erp.objects.filter(user=obj).count()

    get_erp_count_total.short_description = "Tot. ERP"
    get_erp_count_total.admin_order_field = "erp_count_total"

    def get_vote_count(self, obj):
        return obj.vote_count

    get_vote_count.short_description = "Votes"
    get_vote_count.admin_order_field = "vote_count"

    def get_rev_count(self, obj):
        return obj.rev_count

    get_rev_count.short_description = "Rev"
    get_rev_count.admin_order_field = "rev_count"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(vote_count=Count("vote", distinct=True))
            .annotate(rev_count=Count("revision", distinct=True))
        )


# Replace the default UserAdmin with our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
