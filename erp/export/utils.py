from abc import abstractmethod
from typing import List, Tuple

from erp.models import Erp


def map_value_from_schema(schema_enum, data):
    return schema_enum[[y[0] for y in schema_enum].index(data)][0]


def map_list_from_schema(schema_enum, data):
    if not data or not len(data):
        return None

    result = set()
    for d in data:
        choice = schema_enum[[y[0] for y in schema_enum].index(d)][0]
        result.add(choice)

    return list(result)


def map_coords(geom):
    if not geom:
        return None
    return ",".join(map(str, geom.coords))


class BaseExportModel:
    @staticmethod
    @abstractmethod
    def headers():
        ...

    @staticmethod
    @abstractmethod
    def map_from(erp):
        ...


def map_erps_to_json_schema(
    erps: List[Erp],
    export_model,
) -> Tuple[List[str], List[BaseExportModel]]:
    headers = export_model.headers()
    results = [export_model.map_from(erp) for erp in erps if erp.accessibilite]

    return headers, results
