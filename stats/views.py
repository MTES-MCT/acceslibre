import datetime

from django.shortcuts import render

from erp.models import Erp
from stats import queries
from stats.models import GlobalStats


def stats(request):
    erp_qs = Erp.objects.published()
    global_stat = GlobalStats.objects.get()
    return render(
        request,
        "stats/index.html",
        context={
            "current_date": datetime.datetime.now(),
            "nb_published_erps": erp_qs.count(),
            "nb_contributors": queries.get_active_contributors_ids().count(),
            "top_contributors": global_stat.top_contributors,
            "erp_counts_histogram": global_stat.erp_counts_histogram,
        },
    )
