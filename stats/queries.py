from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from core.lib import sql
from erp.models import Erp


def get_erp_counts_histogram():
    results = sql.run_sql(
        """--sql
        select
            date,
            count(a.id) filter (
                where e.created_at <= date + interval '1 day'
                and e.published
            ) as total
        from
            generate_series(current_date - interval '12 months', current_date, interval '1 month') as date
        cross join
            erp_accessibilite a
        left join
            erp_erp e on e.id = a.erp_id
        group by date
        order by date asc;
        """
    )
    return {
        "labels": [r["date"].strftime("%b %Y") for r in results],
        "totals": [r["total"] for r in results],
    }


def get_active_contributors_ids():
    return Erp.objects.published().with_user().values_list("user_id", flat=True).distinct("user_id").order_by("user_id")


def get_top_contributors():
    return (
        get_user_model()
        .objects.annotate(
            erp_count_published=Count("erp", filter=Q(erp__published=True), distinct=True),
            erp_count_total=Count("erp", distinct=True),
        )
        .order_by("-erp_count_published")[:10]
        .values("username", "erp_count_published", "erp_count_total")
    )


def get_count_challenge(start_date, stop_date, emails_players_list):
    filters = Q(
        erp__published=True,
        erp__user__email__in=emails_players_list,
        erp__created_at__gte=start_date,
        erp__created_at__lt=stop_date,
    )
    challengers = get_user_model().objects.filter(email__in=emails_players_list)
    top_contribs = (
        challengers.annotate(erp_count_published=Count("erp", filter=filters, distinct=True))
        .filter(erp_count_published__gt=0)
        .order_by("-erp_count_published")
    )
    total_contributions = sum([c.erp_count_published for c in top_contribs])
    return top_contribs, total_contributions
