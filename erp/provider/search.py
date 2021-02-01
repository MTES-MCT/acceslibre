from erp.models import Commune, Erp
from erp.provider import (
    arrondissements,
    pagesjaunes,
)


def get_searched_commune(code_insee, search):
    commune = Commune.objects.filter(code_insee=code_insee).first()
    if commune:
        return commune.nom
    # lookup arrondissements
    arrdt = arrondissements.get_by_code_insee(code_insee)
    return arrdt["commune"] if arrdt else ""


def sort_and_filter_results(code_insee, results):
    siret_seen = []
    processed = []

    for result in results:
        # Exclude non-geolocalized results
        if result.get("coordonnees") is None:
            continue
        # Exclude results from other departements
        if result.get("code_insee") and result["code_insee"][:2] != code_insee[:2]:
            continue
        # Exclude already seen siret
        siret = result.get("siret")
        if siret:
            if siret in siret_seen:
                continue
            else:
                siret_seen.append(result.get("siret"))
        processed.append(result)

    # Sort with matching commune first (same insee code)
    processed = sorted(
        processed,
        key=lambda result: result["code_insee"] == code_insee,
        reverse=True,
    )

    return processed


def global_search(terms, code_insee):
    # Pagesjaunes
    commune = Commune.objects.get(code_insee=code_insee)
    results_pj = pagesjaunes.search(terms, commune.nom)
    for result in results_pj:
        result["exists"] = Erp.objects.find_by_source_id(
            result["source"], result["source_id"]
        )
    return sort_and_filter_results(code_insee, results_pj)
