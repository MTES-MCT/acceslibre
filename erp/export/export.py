import csv
import json
from dataclasses import asdict
from typing import List, Type

import requests
from django.conf import settings

from core.settings import get_env_variable
from erp.export.utils import BaseExportMapper, map_erps_to_json_schema
from erp.models import Erp

API = "https://www.data.gouv.fr/api/1"
HEADERS = {
    "X-API-KEY": settings.DATAGOUV_API_KEY,
}


def factory(data):
    # Lists in CSV are rendered like "[""value""]", but standard csv module gives '["value"]'
    return dict([(x[0], json.dumps(x[1])) if type(x[1]) == list else x for x in data])


def export_schema_to_csv(file, erps: List[Erp], model: Type[BaseExportMapper]):
    headers, mapped_data = map_erps_to_json_schema(erps, model)
    csv_writer = csv.DictWriter(file, fieldnames=headers)
    csv_writer.writeheader()

    for erp in mapped_data:
        data = asdict(erp, dict_factory=factory)
        csv_writer.writerow(data)


def upload_to_datagouv(csv_path):
    """
    OpenAPI: https://doc.data.gouv.fr/api/reference/#/datasets/upload_dataset_resource
    Documentation: https://doc.data.gouv.fr/api/dataset-workflow/#modification-dun-jeu-de-donn%C3%A9es
    """
    url = f"{API}/datasets/acceslibre/resources/93ae96a7-1db7-4cb4-a9f1-6d778370b640/upload/"

    response = requests.post(
        url,
        files={
            "file": open(csv_path, "rb"),
        },
        headers=HEADERS,
    )

    return response
