import logging

from erp.models import Erp

logger = logging.getLogger(__name__)


def _check_doublons(erp, other):
    return all(
        [erp.get("siret") != other.get("siret"), erp.get("nom") != other.get("nom")]
    )


def parse_etablissements(qs, other_sources):
    datas = qs.values()
    for erp in datas:
        erp.pop("source")
        erp.pop("source_id")
        erp["get_absolute_url"] = Erp.objects.get(pk=erp["id"]).get_absolute_url()
        erp["is_online"] = Erp.objects.get(pk=erp["id"]).is_online()
        erp["icon"] = Erp.objects.get(pk=erp["id"]).get_activite_vector_icon()
        erp["activite"] = Erp.objects.get(pk=erp["id"]).activite
        other_sources = [
            other_erp for other_erp in other_sources if _check_doublons(erp, other_erp)
        ]
    return [
        dict(
            exists={
                "is_online": data["is_online"],
                "get_absolute_url": data["get_absolute_url"],
                "slug": data["slug"],
                "user": data["user_id"],
                "published": data["published"],
                "icon": data["icon"],
                "activite": data["activite"],
            },
            source="acceslibre",
            coordonnees=data["geom"],
            naf=None,
            **data
        )
        for data in datas
    ], other_sources
