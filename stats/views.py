from django.shortcuts import render

from stats import queries
from stats.matomo import MatomoException, get_number_widget_open, get_unique_visitors


def stats(request):
    try:
        nb_unique_visitors = get_unique_visitors(source="beta")
    except MatomoException:
        nb_unique_visitors = None

    try:
        nb_widget_open = get_number_widget_open(source="cloud")
    except MatomoException:
        nb_widget_open = None

    total_published_erps = queries.get_total_published_erps()

    return render(
        request,
        "stats/index.html",
        context={
            "nb_published_erps": total_published_erps,
            "nb_contributors": len(queries.get_active_contributors_ids()),
            "total_erps": queries.get_total_erps_per_month(),
            "average_completion_rate": queries.get_average_completion_rate(),
            "last_12_months_created_or_updated_erps": queries.get_completed_erps_from_last_12_months,
            "erp_completion_totals": queries.get_completion_totals(total_published_erps),
            "nb_unique_visitors": nb_unique_visitors,
            "nb_widget_open": nb_widget_open,
            "page_type": "stats",
        },
    )
