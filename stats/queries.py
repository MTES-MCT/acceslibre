from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from core.lib import sql


def get_erp_counts_histogram():
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


def get_stats_territoires(sort="completude", max=10):
    sort_field = "erps_commune" if sort == "count" else "pourcentage_completude"
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
                {sort_field} desc
            limit {max};
            """
    )


def get_count_active_contributors():
    """Retourne le nombre de contributeurs ayant apporté, modifié au moins une info publiée"""
    return (
        get_user_model()
        .objects.filter(
            Q(
                erp__published=True,
                erp__accessibilite__isnull=False,
                erp__geom__isnull=False,
            )
        )
        .distinct()
        .count()
    )


def get_top_contributors():
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
