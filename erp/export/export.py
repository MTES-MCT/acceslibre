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
    return dict([(x[0], json.dumps(x[1])) if isinstance(x[1], list) else x for x in data])


def _write_csv(csv_writer, erps: List[Erp], model: Type[BaseExportMapper], logger=None):
    if logger:
        logger("Écriture des entêtes")
    csv_writer.writeheader()

    for erp_data in map_erps_to_json_schema(erps, model):
        if logger:
            logger(f"\t * Ajout de l'ERP {erp_data.name}")
        data = asdict(erp_data, dict_factory=factory)
        csv_writer.writerow(data)


def export_schema_to_csv(file_path, erps: List[Erp], model: Type[BaseExportMapper], logger=None):
    with open(file_path, "w", newline="") as csv_file:
        if logger:
            logger(f"Initialisation du csv {file_path}")
        csv_writer = csv.DictWriter(csv_file, fieldnames=model.headers())
        _write_csv(csv_writer, erps, model, logger)


def export_schema_to_buffer(buffer, erps: List[Erp], model: Type[BaseExportMapper]):
    csv_writer = csv.DictWriter(buffer, fieldnames=model.headers())
    _write_csv(csv_writer, erps, model)


def upload_to_datagouv(
    csv_path,
    dataset_id=settings.DATAGOUV_DATASET_ID,
    resources_id=settings.DATAGOUV_RESOURCES_ID,
):
    """
    OpenAPI: https://doc.data.gouv.fr/api/reference/#/datasets/upload_dataset_resource
    Documentation: https://doc.data.gouv.fr/api/dataset-workflow/#modification-dun-jeu-de-donn%C3%A9es
    """
    if not settings.DATAGOUV_API_KEY:
        return

    url = "{domain}/api/1/datasets/{dataset_id}/resources/{resources_id}/upload/".format(
        domain=settings.DATAGOUV_DOMAIN,
        dataset_id=dataset_id,
        resources_id=resources_id,
    )

    try:
        response = requests.post(
            url,
            files={"file": open(csv_path, "rb")},
            headers={"X-API-KEY": settings.DATAGOUV_API_KEY},
        )
        response.raise_for_status()
        assert response.json().get("success")
    except (
        requests.RequestException,
        json.JSONDecodeError,
        AssertionError,
    ) as err:
        raise RuntimeError(f"Erreur lors de l'upload: {err}")

    return True
