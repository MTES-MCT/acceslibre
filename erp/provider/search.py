from core.lib.text import remove_accents
from erp.models import Commune, Erp
from erp.provider import entreprise, public_erp


def prepare_terms(s):
    return [t.lower() for t in remove_accents(s).split(" ")]


def find_public_type(search):
    terms = prepare_terms(search)
    for key, val in public_erp.TYPES.items():
        for term in terms:
            if term == key or term in prepare_terms(val):
                return key


def find_global_erps(form):
    search = form.cleaned_data.get("search")
    code_insee = form.cleaned_data.get("code_insee")
    commune = Commune.objects.filter(code_insee=code_insee).first()
    search = f"{search} {commune.nom}" if commune else search

    # Entreprise
    result_entreprises = entreprise.search(search)
    for result in result_entreprises:
        result["exists"] = Erp.objects.find_by_siret(result["siret"])

    # Administration publique
    result_public = []
    found_public_type = find_public_type(search)
    if found_public_type:
        result_public = public_erp.get_code_insee_type(
            code_insee,
            found_public_type,
        )
        for result in result_public:
            result["exists"] = Erp.objects.find_by_source_id(
                result["source"], result["source_id"]
            )
    return result_entreprises + result_public
