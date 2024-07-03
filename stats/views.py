from django.shortcuts import render

from erp.models import Erp
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

    return render(
        request,
        "stats/index.html",
        context={
            "nb_published_erps": Erp.objects.published().count(),
            "nb_contributors": queries.get_active_contributors_ids().count(),
            "nb_unique_visitors": nb_unique_visitors,
            "nb_widget_open": nb_widget_open,
        },
    )
