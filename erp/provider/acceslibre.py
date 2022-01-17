import logging

from erp.models import Erp

logger = logging.getLogger(__name__)


def parse_etablissements(qs, other_sources):
    datas = qs.values()
    for erp in datas:
        erp.pop("source")
        erp.pop("source_id")
        siret = erp.get("siret")
        erp["get_absolute_url"] = Erp.objects.get(pk=erp["id"]).get_absolute_url()
        erp["is_online"] = Erp.objects.get(pk=erp["id"]).is_online()
        other_sources = [
            other_erp for other_erp in other_sources if other_erp["siret"] != siret
        ]
    return [
        dict(
            exists={
                "is_online": data["is_online"],
                "get_absolute_url": data["get_absolute_url"],
                "slug": data["slug"],
                "user": data["user_id"],
                "published": data["published"],
            },
            source="acceslibre",
            coordonnees=data["geom"],
            naf=None,
            **data
        )
        for data in datas
    ], other_sources
