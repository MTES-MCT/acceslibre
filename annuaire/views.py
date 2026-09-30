from collections import defaultdict

from django.db.models import Count
from django.http import Http404
from django.shortcuts import render

from erp.models import Commune, Erp
from erp.provider import arrondissements, departements


def home(request):
    return render(
        request,
        "annuaire/index.html",
        context={"departements": departements.get_departements()},
    )


def _get_parent_nom(commune):
    if not commune.arrondissement:
        return None
    return (arrondissements.get_by_code_insee(commune.code_insee) or {}).get("commune")


def _group_arrondissements(communes, arrondissement_communes):
    """Group the communes having arrondissements (Paris, Lyon, Marseille) with their arrondissements.

    NOTE most erps of those cities are attached to the parent commune (eg. Paris) and not to their
    arrondissement, so the erps of the parent are attributed to its arrondissements by code postal.
    """
    communes = list(communes)
    arrondissement_by_parent = defaultdict(list)
    for commune in arrondissement_communes:
        parent_nom = _get_parent_nom(commune)
        if parent_nom:
            arrondissement_by_parent[parent_nom].append(commune)

    if not arrondissement_by_parent:
        return communes

    parents = [commune for commune in communes if commune.nom in arrondissement_by_parent]
    erp_count_by_postal = defaultdict(dict)
    for row in (
        Erp.objects.published()
        .filter(commune_ext__in=parents)
        .values("commune_ext_id", "code_postal")
        .annotate(count=Count("id"))
    ):
        erp_count_by_postal[row["commune_ext_id"]][row["code_postal"]] = row["count"]

    attached_arrondissements = set()
    for commune in parents:
        count_by_postal = erp_count_by_postal.get(commune.pk, {})
        commune.arrondissements = []
        # NOTE the parent count includes the erps already attached to one of its arrondissements
        parent_erp_count = commune.erp_access_count
        for arrondissement in sorted(arrondissement_by_parent[commune.nom], key=lambda c: c.code_insee):
            code_postal = (arrondissement.code_postaux or [None])[0]
            parent_erp_count += arrondissement.erp_access_count
            arrondissement.erp_access_count += count_by_postal.get(code_postal, 0)
            if arrondissement.erp_access_count > 0:
                commune.arrondissements.append(arrondissement)
                attached_arrondissements.add(arrondissement.pk)
        commune.erp_access_count = parent_erp_count

    return [commune for commune in communes if not commune.arrondissement or commune.pk not in attached_arrondissements]


def departement(request, departement):
    departements_list = departements.get_departements()
    current_departement = departements_list.get(departement)
    if not current_departement:
        raise Http404(f"departement inconnu: {departement}")
    current_departement["code"] = departement
    communes = _group_arrondissements(
        Commune.objects.with_published_erp_count().filter(departement=departement, erp_access_count__gt=0),
        Commune.objects.with_published_erp_count().filter(departement=departement, arrondissement=True),
    )
    return render(
        request,
        "annuaire/index.html",
        context={
            "departements": departements_list,
            "current_departement": current_departement,
            "current_departement_erp_count": Erp.objects.published()
            .filter(commune_ext__departement=current_departement["code"])
            .count(),
            "communes": communes,
        },
    )
