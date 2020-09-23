import datetime

from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import Count
from django.utils import timezone
from django.views.generic import TemplateView

from erp.models import Commune, Erp, Vote


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    # https://docs.djangoproject.com/en/3.1/topics/db/sql/#executing-custom-sql-directly
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def run_sql(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return dictfetchall(cursor)


class StatsView(TemplateView):
    template_name = "stats/index.html"

    def get_date_range(self):
        base = timezone.now()
        lst = [base - datetime.timedelta(days=x) for x in range(30)]
        lst.reverse()
        return lst

    def get_nb_contributors(self):
        return run_sql(
            """--sql
            select count(distinct e.user_id)
            from erp_erp e
            left join erp_accessibilite a on a.erp_id = e.id
            where e.geom is not null and a.id is not null;
            """
        )[0].get("count", 0)

    def get_top_contributors(self):
        return (
            get_user_model()
            .objects.annotate(erp_count=Count("erp", distinct=True))
            .filter(erp__accessibilite__isnull=False)
            .order_by("-erp_count")[:10]
        )

    def get_top_voters(self):
        return (
            get_user_model()
            .objects.annotate(vote_count=Count("vote", distinct=True))
            .exclude(vote_count=0)
            .order_by("-vote_count")[:10]
        )

    def get_north_star(self):
        vote_qs = Vote.objects
        positive = vote_qs.filter(value=1).count()
        total = vote_qs.count()
        percent = (positive / total * 100) if total != 0 else 100
        return {
            "positive": positive,
            "total": total,
            "percent": percent,
        }

    def get_votes_histogram(self):
        results = run_sql(
            """--sql
            select
                count(erp_vote.id) as total,
                count(erp_vote.id) filter (where erp_vote.value = 1) as positive,
                date
            from
                erp_vote,
                generate_series(current_date - interval '30 day', current_date, interval '1 day') as date
            where erp_vote.created_at <= date
            group by date
            order by date ASC;
            """
        )
        return {
            "labels": [r["date"].strftime("%Y-%m-%d") for r in results],
            "totals": [r["total"] for r in results],
            "positives": [r["positive"] for r in results],
        }

    def get_erp_counts_histogram(self):
        results = run_sql(
            """--sql
            select
                date,
                count(a.id) filter (
                    where e.created_at <= date
                    and e.geom is not null
                    and e.published
                ) as total
            from
                generate_series(current_date - interval '30 day', current_date, interval '1 day') as date
            cross join
                erp_accessibilite a
            left join
                erp_erp e on e.id = a.erp_id
            group by date
            order by date asc;
            """
        )
        return {
            "labels": [r["date"].strftime("%Y-%m-%d") for r in results],
            "totals": [r["total"] for r in results],
        }

    def get_contributors_histogram(self):
        results = run_sql(
            """--sql
            select
                date,
                count(distinct e.user_id) filter (
                    where e.created_at <= date
                ) as total
            from
                generate_series(current_date - interval '30 day', current_date, interval '1 day') as date
            cross join
                erp_accessibilite a
            left join
                erp_erp e on e.id = a.erp_id
            where e.geom is not null
            group by date
            order by date asc;
            """
        )
        return {
            "labels": [r["date"].strftime("%Y-%m-%d") for r in results],
            "totals": [r["total"] for r in results],
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        erp_qs = Erp.objects.published()

        context["north_star"] = self.get_north_star()
        context["nb_filled_erps"] = erp_qs.count()
        context["communes"] = Commune.objects.erp_stats()[:10]
        context["nb_contributors"] = self.get_nb_contributors()
        context["top_contributors"] = self.get_top_contributors()
        context["top_voters"] = self.get_top_voters()
        context["votes_histogram"] = self.get_votes_histogram()
        context["erp_counts_histogram"] = self.get_erp_counts_histogram()
        context["contributors_histogram"] = self.get_contributors_histogram()

        return context
