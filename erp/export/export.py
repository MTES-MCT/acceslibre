import csv
import json
from dataclasses import asdict
from typing import List, Type

from erp.export.utils import BaseExportModel, map_erps_to_json_schema
from erp.models import Erp


def factory(data):
    # Lists in CSV are rendered like "[""value""]", but standard csv module gives '["value"]'
    return dict([(x[0], json.dumps(x[1])) if type(x[1]) == list else x for x in data])


def export_schema_to_csv(file, erps: List[Erp], model: Type[BaseExportModel]):
    headers, mapped_data = map_erps_to_json_schema(erps, model)
    csv_writer = csv.DictWriter(file, fieldnames=headers)
    csv_writer.writeheader()

    for erp in mapped_data:
        data = asdict(erp, dict_factory=factory)
        csv_writer.writerow(data)
