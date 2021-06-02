import datetime

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import TemplateView

from core.lib import sql
from erp.models import Activite, Commune, Erp, Vote


class ObjectifsView(TemplateView):
    template_name = "stats/objectifs.html"

    def get_stats_objectifs(self):
        return sql.run_sql(
            """--sql
            select
                (data.erps_commune::float / data.total_erps_commune::float * 100::float) as pourcentage_completude,
                * from (
                    select
                        c.nom,
                        c.slug,
                        c.code_insee,
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
                        c.nom, c.slug, c.code_insee, c.population, c.departement
                ) data
            where
                data.population > 5000 and data.erps_commune > 0 and data.total_erps_commune > 0
            order by
                pourcentage_completude desc
            limit 20;
            """
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats_objectifs"] = self.get_stats_objectifs()
        return context


class StatsView(TemplateView):
    template_name = "stats/index.html"

    def get_date_range(self):
        base = timezone.now()
        lst = [base - datetime.timedelta(days=x) for x in range(30)]
        lst.reverse()
        return lst

    def get_nb_contributors(self):
        return sql.run_sql(
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
        results = sql.run_sql(
            """--sql
            select
                count(erp_vote.id) as total,
                count(erp_vote.id) filter (where erp_vote.value = 1) as positive,
                date
            from
                erp_vote,
                generate_series(current_date - interval '30 day', current_date, interval '1 day') as date
            where erp_vote.created_at <= date + interval '1 day'
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
        results = sql.run_sql(
            """--sql
            select
                date,
                count(distinct e.user_id) filter (
                    where e.created_at <= date + interval '1 day'
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
        context["nb_published_erps"] = erp_qs.count()
        context["nb_published_erps_by_users"] = erp_qs.filter(
            user__isnull=False
        ).count()
        context["nb_filled_erps"] = erp_qs.having_a11y_data().count()
        # vaccination centers
        cv = Activite.objects.get(slug="centre-de-vaccination")
        context["nb_cv_erps"] = erp_qs.filter(activite=cv).count()
        context["nb_cv_filled_erps"] = (
            erp_qs.filter(activite=cv).having_a11y_data().count()
        )
        context["communes"] = Commune.objects.erp_stats()[:10]
        context["nb_communes"] = (
            Commune.objects.erp_stats().filter(erp_access_count__gt=0).count()
        )
        context["nb_users"] = get_user_model().objects.filter(is_active=True).count()
        context["nb_contributors"] = self.get_nb_contributors()
        context["top_contributors"] = self.get_top_contributors()
        context["top_voters"] = self.get_top_voters()
        context["votes_histogram"] = self.get_votes_histogram()
        context["erp_counts_histogram"] = self.get_erp_counts_histogram()
        context["contributors_histogram"] = self.get_contributors_histogram()

        return context
