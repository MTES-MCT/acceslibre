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


def get_count_challenge(start_date, stop_date):
    emails_players_list = [
        "gauthierlaprade@gmail.com",
        "magali.vainjac@savoie.gouv.fr",
        "roxane.herin@savoie.gouv.fr",
        "christel.condemine@savoie.gouv.fr",
        "jean-christophe.henrotte@savoie.gouv.fr",
        "sophie.lucas@aube.gouv.fr",
        "frederic.chaal@aube.gouv.fr",
        "thomas.lapierre@aube.gouv.fr",
        "sabine.lemoine@aube.gouv.fr",
        "stephane.mulat@aube.gouv.fr",
        "carine.rudelle@aveyron.gouv.fr",
        "veronique.bex@aveyron.gouv.fr",
        "nadine.negre@aveyron.gouv.fr",
        "bernadette.denoit@aveyron.gouv.fr",
        "emmanuelle.esteve-chellali@aveyron.gouv.fr",
        "ddt-sh@haute-savoie.gouv.fr",
        "lea.pelissier@haute-savoie.gouv.fr",
        "martine.excoffier@haute-savoie.gouv.fr",
        "josiane.tomasin@haute-savoie.gouv.fr",
        "jerome.ramanzin@haute-savoie.gouv.fr",
        "sophie.tcheng@developpement-durable.gouv.fr",
        "gauthier.laprade@i-carre.net",
        "laurence.monnet@developpement-durable.gouv.fr",
        "delphine.millot@meuse.gouv.fr",
        "ddt-scdt-ats@meuse.gouv.fr",
        "christelle.defloraine@meuse.gouv.fr",
        "catherine.pasquier@meuse.gouv.fr",
        "sophie.barbet@landes.gouv.fr",
        "corinne.loubere@landes.gouv.fr",
        "laure.delerce@landes.gouv.fr",
        "sophie.batifoulier@landes.gouv.fr",
        "isabelle.plagnes@sfr.fr",
        "romain.gaeta@loire-atlantique.gouv.fr",
        "Olivier.claireau@sfr.fr",
        "franck.menard@loire-atlantique.gouv.fr",
        "veronique.laune@loire-atlantique.gouv.fr",
        "ddtm-vserp@loire-atlantique.gouv.fr",
        "thierry.mocogni@eure-et-loir.gouv.fr",
        "isabelle.desile@eure-et-loir.gouv.fr",
        "odile.gomme@eure-et-loir.gouv.fr",
        "jean-philippe.renard@eure-et-loir.gouv.fr",
        "sandra.tachat@eure-et-loir.gouv.fr",
        "philippejos09@hotmail.fr",
        "lilimag.29@gmail.com",
        "construction.durable82@gmail.com",
        "rivagali@hotmail.com",
        "nathalie.cauleur@saone-et-loire.gouv.fr",
        "lucie.pagat@saone-et-loire.gouv.fr",
        "jerome.laville@saone-et-loire.gouv.fr",
        "didier.bonnefoy@saone-et-loire.gouv.fr",
        "axel.schalk@saone-et-loire.gouv.fr",
        "colette.py@haut-rhin.gouv.fr",
        "isabelle.pla@haut-rhin.gouv.fr",
        "danielle.guillaume@haut-rhin.gouv.fr",
        "patrick.reibel@haut-rhin.gouv.fr",
        "stparfait18@hotmail.fr",
        "zohra.benzaghou@jura.gouv.fr",
        "emilie.gauthier@jura.gouv.fr",
        "franck.villet@jura.gouv.fr",
        "thomas.brante@jura.gouv.fr",
        "olivier.decharriere@jura.gouv.fr",
        "max.palix@ardeche.gouv.fr",
        "nathalie.chauvin@ardeche.gouv.fr",
        "mireille.gay@ardeche.gouv.fr",
        "valerie.lafont@ardeche.gouv.fr",
        "magali.aubert@ardeche.gouv.fr",
        "sebastien.charles@marne.gouv.fr",
        "francois-xavier.bouilleret@marne.gouv.fr",
        "jean-michel.demorat@marne.gouv.fr",
        "piero.osti@marne.gouv.fr",
        "damien.thomassin@ain.gouv.fr",
        "fabienne.olivier@ain.gouv.fr",
        "yahya.ettoubi@ain.gouv.fr",
        "daniel.clerc@ain.gouv.fr",
        "sebastien.guichon@ain.gouv.fr",
        "sarah.debrabant@rhone.gouv.fr",
        "barbara.bonelli@rhone.gouv.fr",
        "sylvie.chanut@rhone.gouv.fr",
        "claire.vancauwemberge@rhone.gouv.fr",
        "thierry.morel@rhone.gouv.fr",
    ]
    filters = Q(
        erp__published=True,
        erp__accessibilite__isnull=False,
        erp__geom__isnull=False,
        erp__user__email__in=emails_players_list,
        erp__created_at__gte=start_date,
        erp__created_at__lt=stop_date,
    )
    top_contribs = (
        get_user_model()
        .objects.annotate(
            erp_count_published=Count(
                "erp",
                filter=filters,
                distinct=True,
            )
        )
        .filter(filters)
        .filter(erp_count_published__gt=0)
        .order_by("-erp_count_published")
    )
    total_contributions = sum([c.erp_count_published for c in top_contribs])
    return top_contribs, total_contributions
