from fuzzywuzzy import process

from core.lib.text import remove_accents
from erp.models import Commune, Erp
from erp.provider import entreprise, public_erp


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


def find_global_erps(form):
    search = form.cleaned_data.get("search")
    code_insee = form.cleaned_data.get("code_insee")
    commune = Commune.objects.filter(code_insee=code_insee).first()
    search_entreprise = f"{search} {commune.nom}" if commune else search

    # Entreprise
    result_entreprises = []
    try:
        result_entreprises = entreprise.search(search_entreprise)
        for result in result_entreprises:
            result["exists"] = Erp.objects.find_by_siret(result["siret"])
    except RuntimeError:
        pass

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
    return result_public + result_entreprises
