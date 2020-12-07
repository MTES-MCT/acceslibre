from erp.models import Commune, Erp
from erp.provider import arrondissements, entreprise, public_erp, opendatasoft


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

    # Exclude results from other departements
    def filter_dpt(result):
        return result["code_insee"][:2] == code_insee[:2]

    results = filter(filter_dpt, results)

    # Sort with matching commune first
    return sorted(
        results,
        key=lambda result: result["code_insee"] == code_insee,
        reverse=True,
    )


def global_search(terms, code_insee):
    # OpenDataSoft
    result_ods = opendatasoft.search(terms, code_insee)
    for result in result_ods:
        result["exists"] = Erp.objects.find_by_siret(result["siret"])

    # Etalab entreprise
    search_entreprises = f"{terms} {get_searched_commune(code_insee, terms)}"
    result_entreprises = entreprise.search(search_entreprises, code_insee)
    for result in result_entreprises:
        result["exists"] = Erp.objects.find_by_siret(result["siret"])

    # Administration publique
    result_public = public_erp.search(terms, code_insee)
    for result in result_public:
        result["exists"] = Erp.objects.find_by_source_id(
            result["source"], result["source_id"]
        )

    return sort_and_filter_results(
        code_insee, result_public + result_ods + result_entreprises
    )
