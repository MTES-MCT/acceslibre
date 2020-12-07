from fuzzywuzzy import process

from core.lib.text import remove_accents
from erp.models import Commune, Erp
from erp.provider import arrondissements, entreprise, public_erp, opendatasoft


MAX_TYPES = 5
MIN_SCORE = 70


def find_public_types(search):
    results = []
    clean = remove_accents(search).lower()
    for key, val in public_erp.TYPES.items():
        searches = [key, val["description"]] + val.get("searches", [])
        (found, score) = process.extractOne(clean, searches)
        results.append({"score": score, "type": key})
    _sorted = sorted(results, key=lambda x: x["score"], reverse=True)
    return [r["type"] for r in _sorted if r["score"] > MIN_SCORE][:MAX_TYPES]


def get_searched_commune(code_insee, search):
    commune = Commune.objects.filter(code_insee=code_insee).first()
    if commune:
        return commune.nom
    # lookup arrondissements
    arrdt = arrondissements.get_by_code_insee(code_insee)
    return arrdt["commune"] if arrdt else ""


def sort_and_filter_results(code_insee, results):
    # Exclude non-geolocalized results
    results = filter(
        lambda result: result.get("coordonnees") is not None,
        results,
    )

    def filter_dpt(result):
        return result["code_insee"][:2] == code_insee[:2]

    # Exclude results from other departements
    results = filter(
        filter_dpt,
        results,
    )
    # Sort with matching commune first
    return sorted(
        results,
        key=lambda result: result["code_insee"] == code_insee,
        reverse=True,
    )


def find_global_erps(form):
    search = form.cleaned_data.get("search")
    code_insee = form.cleaned_data.get("code_insee")
    search_entreprise = f"{search} {get_searched_commune(code_insee, search)}"

    # Entreprise
    result_entreprises = entreprise.search(search_entreprise, code_insee)
    for result in result_entreprises:
        result["exists"] = Erp.objects.find_by_siret(result["siret"])

    # OpenDataSoft
    result_ods = opendatasoft.search(search_entreprise, code_insee)
    for result in result_ods:
        result["exists"] = Erp.objects.find_by_siret(result["siret"])

    # Administration publique
    result_public = []
    found_public_types = find_public_types(search)
    for public_type in found_public_types:
        try:
            tmp_results = public_erp.get_code_insee_type(code_insee, public_type)
            for result in tmp_results:
                if result and code_insee == result["code_insee"]:
                    result["exists"] = Erp.objects.find_by_source_id(
                        result["source"], result["source_id"]
                    )
                    result_public.append(result)
        except RuntimeError:
            pass
    return sort_and_filter_results(
        code_insee, result_public + result_ods + result_entreprises
    )
