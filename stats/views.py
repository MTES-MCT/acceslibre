from django.shortcuts import render

from erp.models import Erp
from stats import queries
from stats.matomo import MatomoException, get_number_widget_open, get_unique_visitors
from stats.metabase import (
    get_total_erps,
    MetabaseException,
    get_average_completion_rate,
    get_last_12_months_created_or_updated_erps,
    get_erp_completion_totals,
)


def stats(request):
    try:
        nb_unique_visitors = get_unique_visitors(source="beta")
    except MatomoException:
        nb_unique_visitors = None

    try:
        nb_widget_open = get_number_widget_open(source="cloud")
    except MatomoException:
        nb_widget_open = None

    try:
        total_erps = get_total_erps()
    except MetabaseException:
        total_erps = None

    try:
        average_completion_rate = get_average_completion_rate()
    except MetabaseException:
        average_completion_rate = None

    try:
        last_12_months_created_or_updated_erps = get_last_12_months_created_or_updated_erps()
    except MetabaseException:
        last_12_months_created_or_updated_erps = None

    try:
        erp_completion_totals = get_erp_completion_totals()
    except MetabaseException:
        erp_completion_totals = None

    return render(
        request,
        "stats/index.html",
        context={
            "nb_published_erps": Erp.objects.published().count(),
            "nb_contributors": queries.get_active_contributors_ids().count(),
            "total_erps": total_erps,
            "average_completion_rate": average_completion_rate,
            "last_12_months_created_or_updated_erps": last_12_months_created_or_updated_erps,
            "erp_completion_totals": erp_completion_totals,
            "nb_unique_visitors": nb_unique_visitors,
            "nb_widget_open": nb_widget_open,
            "page_type": "stats",
        },
    )
