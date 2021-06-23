import datetime

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import TemplateView

from core.lib import sql
from erp.models import Erp


def get_stats_territoires(max=10):
    return sql.run_sql(
        f"""--sql
            select
                (data.erps_commune::float / data.total_erps_commune::float * 100::float) as pourcentage_completude,
                * from (
                    select
                        c.nom,
                        c.slug,
                        c.population,
                        c.departement,
                        (c.population / 45) as total_erps_commune,
                        COUNT(e.id) filter (
                            where e.geom is not null
                            and e.published
                            and a.id is not null
                        ) as erps_commune
                    from
                        erp_commune c
                    left join
                        erp_erp e on e.commune_ext_id = c.id
                    left join
                        erp_accessibilite a on e.id = a.erp_id
                    where
                        c.population >= 0
                    group by
                        c.nom, c.slug, c.population, c.departement
                ) data
            where
                data.population > 5000 and data.erps_commune > 0 and data.total_erps_commune > 0
            order by
                pourcentage_completude desc
            limit {max};
            """
    )


class TerritoiresView(TemplateView):
    template_name = "stats/territoires.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["palmares"] = get_stats_territoires(max=50)
        return context


class StatsView(TemplateView):
    template_name = "stats/index.html"

    def get_date_range(self):
        base = timezone.now()
        lst = [base - datetime.timedelta(days=x) for x in range(30)]
        lst.reverse()
        return lst

    def get_top_contributors(self):
        return (
            get_user_model()
            .objects.annotate(
                erp_count_published=Count(
                    "erp",
                    filter=Q(
                        erp__published=True,
                        erp__accessibilite__isnull=False,
                        erp__geom__isnull=False,
                    ),
                    distinct=True,
                ),
                erp_count_total=Count(
                    "erp",
                    distinct=True,
                ),
            )
            .filter(erp__accessibilite__isnull=False)
            .order_by("-erp_count_published")[:10]
            .values("username", "erp_count_published", "erp_count_total")
        )

    def get_erp_counts_histogram(self):
        results = sql.run_sql(
            """--sql
            select
                date,
                count(a.id) filter (
                    where e.created_at <= date + interval '1 day'
                    and e.geom is not null
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        erp_qs = Erp.objects.published()

        context["current_date"] = datetime.datetime.now()
        context["nb_published_erps"] = erp_qs.count()
        context["top_contributors"] = self.get_top_contributors()
        context["erp_counts_histogram"] = self.get_erp_counts_histogram()
        context["palmares"] = get_stats_territoires()

        return context
