import datetime

from django.shortcuts import render

from erp.models import Erp
from stats import queries
from stats.models import GlobalStats


def stats(request):
    sort = _get_sort(request)
    erp_qs = Erp.objects.published()
    global_stat = GlobalStats.objects.get()
    return render(
        request,
        "stats/index.html",
        context={
            "current_date": datetime.datetime.now(),
            "nb_published_erps": erp_qs.count(),
            "nb_contributors": queries.get_active_contributors().count(),
            "top_contributors": global_stat.top_contributors,
            "erp_counts_histogram": global_stat.erp_counts_histogram,
            "stats_territoires": global_stat.get_stats_territoires(sort=sort)[:10],
            "stats_territoires_sort": sort,
        },
    )


def territoires(request):
    sort = _get_sort(request)
    global_stat = GlobalStats.objects.get()
    return render(
        request,
        "stats/territoires.html",
        context={
            "stats_territoires": global_stat.get_stats_territoires(sort=sort),
            "stats_territoires_sort": sort,
        },
    )


def _get_sort(request):
    return "count" if request.GET.get("sort") == "count" else "completude"
