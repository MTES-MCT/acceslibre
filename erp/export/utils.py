from abc import abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple, Type, TypeVar

from erp.models import Erp

Mapper = TypeVar("Mapper")


@dataclass(frozen=True)
class BaseExportMapper:
    @staticmethod
    @abstractmethod
    def headers():
        pass

    @staticmethod
    @abstractmethod
    def map_from(erp):
        pass


def map_erps_to_json_schema(
    erps: List[Erp],
    export_model: Type[Mapper],
) -> Tuple[List[str], List[Mapper]]:
    for erp in erps.iterator(chunk_size=500):
        if getattr(erp, "accessibilite", None):
            yield export_model.map_from(erp)


def map_value_from_schema(schema_enum, data):
    return schema_enum[[y[0] for y in schema_enum].index(data)][0]


def map_list_from_schema(schema_enum, data, verbose=False):
    if verbose:
        index = 1
    else:
        index = 0

    if not data:
        return None

    result = []
    for d in data:
        choice = schema_enum[[y[0] for y in schema_enum].index(d)][index]
        result.append(str(choice))

    return list(dict.fromkeys(result))


def map_coords(geom, index) -> Optional[float]:
    if not geom:
        return None
    return geom.coords[index]
