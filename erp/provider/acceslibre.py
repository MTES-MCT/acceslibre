import logging

from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)


def _not_duplicate(erp, other):
    return all([erp.get("siret") != other.get("siret"), erp.get("nom") != other.get("nom")])


def parse_etablissements(qs, other_sources):
    for erp in qs.iterator(chunk_size=200):
        erp_as_dict = model_to_dict(erp)
        erp_as_dict.pop("source")
        erp_as_dict.pop("source_id")
        erp_as_dict["get_absolute_url"] = erp.get_absolute_url()
        erp_as_dict["icon"] = erp.get_activite_vector_icon()
        erp_as_dict["activite"] = erp.activite
        other_sources = [other_erp for other_erp in other_sources if _not_duplicate(erp_as_dict, other_erp)]
    return other_sources
