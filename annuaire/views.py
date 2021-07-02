from django.http import Http404
from django.shortcuts import render

from erp.models import Commune, Erp
from erp.provider import departements


def home(request):
    return render(
        request,
        "annuaire/index.html",
        context={"departements": departements.get_departements()},
    )


def departement(request, departement):
    departements_list = departements.get_departements()
    current_departement = departements_list.get(departement)
    if not current_departement:
        raise Http404(f"departement inconnu: {departement}")
    current_departement["code"] = departement
    return render(
        request,
        "annuaire/index.html",
        context={
            "departements": departements_list,
            "current_departement": current_departement,
            "current_departement_erp_count": Erp.objects.published()
            .filter(commune_ext__departement=current_departement["code"])
            .count(),
            "communes": Commune.objects.with_published_erp_count()
            .filter(departement=departement, erp_access_count__gt=0)
            .order_by("nom"),
        },
    )
