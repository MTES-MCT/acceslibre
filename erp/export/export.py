import csv
import json
from dataclasses import asdict
from typing import List, Type

import requests
from django.conf import settings

from erp.export.utils import BaseExportMapper, map_erps_to_json_schema
from erp.models import Erp


def factory(data):
    # Lists in CSV are rendered like "[""value""]", but standard csv module gives '["value"]'
    return dict([(x[0], json.dumps(x[1])) if type(x[1]) == list else x for x in data])


def export_schema_to_csv(file_path, erps: List[Erp], model: Type[BaseExportMapper]):
    with open(file_path, "w", newline="") as csv_file:
        headers, mapped_data = map_erps_to_json_schema(erps, model)
        csv_writer = csv.DictWriter(csv_file, fieldnames=headers)
        csv_writer.writeheader()

        for erp in mapped_data:
            data = asdict(erp, dict_factory=factory)
            csv_writer.writerow(data)


def upload_to_datagouv(csv_path):
    """
    OpenAPI: https://doc.data.gouv.fr/api/reference/#/datasets/upload_dataset_resource
    Documentation: https://doc.data.gouv.fr/api/dataset-workflow/#modification-dun-jeu-de-donn%C3%A9es
    """
    if not settings.DATAGOUV_API_KEY:
        return

    url = f"{settings.DATAGOUV_DOMAIN}/api/1/datasets/acceslibre/resources/{settings.DATAGOUV_DATASET_ID}/upload/"

    try:
        response = requests.post(
            url,
            files={"file": open(csv_path, "rb")},
            headers={"X-API-KEY": settings.DATAGOUV_API_KEY},
        )
        response.raise_for_status()
    except (
        requests.exceptions.RequestException,
        requests.exceptions.Timeout,
        json.JSONDecodeError,
        requests.exceptions.HTTPError,
    ) as err:
        raise RuntimeError(err)

    assert response.json().get("success")
    return True
