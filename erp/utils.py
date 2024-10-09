import re

from django.contrib.gis.geos import Polygon
from django.utils.translation import gettext as translate

from erp.models import Erp
from erp.provider.search import filter_erp_by_location, filter_erps_by_equipments


def cleaned_search_params_as_dict(get_parameters):
    allow_list = ("where", "what", "lat", "lon", "code", "search_type", "postcode", "street_name", "municipality")
    cleaned_dict = {
        k: "" if get_parameters.get(k, "") == "None" else get_parameters.get(k, "")
        for k, v in get_parameters.items()
        if k in allow_list
    }
    cleaned_dict["where"] = cleaned_dict.get("where") or translate("France entière")
    return cleaned_dict


def build_queryset(filters, request_get, with_zone=False):
    base_queryset = Erp.objects.published().with_activity()
    base_queryset = base_queryset.search_what(filters.get("what"))
    if "where" in filters:
        filters["city"], filters["code_departement"] = clean_address(filters.get("where"))

    queryset = filter_erp_by_location(base_queryset, **filters)
    queryset = filter_erps_by_equipments(queryset, request_get.getlist("equipments", []))
    if with_zone and "zone" in request_get:
        min_lng, min_lat, max_lng, max_lat = map(float, request_get["zone"].split(","))
        bbox_polygon = Polygon.from_bbox((min_lng, min_lat, max_lng, max_lat))
        queryset = queryset.filter(geom__within=bbox_polygon)

    return queryset


def clean_address(where):
    """
    where is a string as returned by geoloc API on frontend side. It returns city and code_departement, this is pure string
    work, nothing coming from a database or elsewhere.
    For ex:
        "Paris (75006)" returns ("Paris", "75")
        "Lille (59)" returns ("Lille", "59")
        "Strasbourg" returns ("Strasbourg", "")
        "10 Rue Marin 69160 Tassin-la-Demi-Lune" returns ("Tassin-la-Demi-Lune", "")
    """
    where = (where or "()").strip()

    # remove code departement in where
    address = re.split(r"\(|\)", where)
    city = where
    code_departement = ""
    if len(address) >= 2:
        city = address[0].strip()
        code_departement = address[1]
    elif found := re.search(r".* [0-9]{5} (.*)", where):
        city = found.groups(1)[0]
    return city, code_departement
