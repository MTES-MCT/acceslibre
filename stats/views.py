import datetime

from django.shortcuts import render

from erp.models import Erp
from stats import queries


def stats(request):
    sort = _get_sort(request)
    erp_qs = Erp.objects.published()
    return render(
        request,
        "stats/index.html",
        context={
            "current_date": datetime.datetime.now(),
            "nb_published_erps": erp_qs.count(),
            "nb_contributors": queries.get_count_active_contributors(),
            "top_contributors": queries.get_top_contributors(),
            "erp_counts_histogram": queries.get_erp_counts_histogram(),
            "stats_territoires": queries.get_stats_territoires(sort=sort),
            "stats_territoires_sort": sort,
        },
    )


def territoires(request):
    sort = _get_sort(request)
    return render(
        request,
        "stats/territoires.html",
        context={
            "stats_territoires": queries.get_stats_territoires(sort=sort, max=50),
            "stats_territoires_sort": sort,
        },
    )


def _get_sort(request):
    return "count" if request.GET.get("sort") == "count" else "completude"
