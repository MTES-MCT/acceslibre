import csv
import json
import re
from dataclasses import asdict
from typing import Generator, List, Type

import requests
from django.conf import settings
from rest_framework_xml.renderers import XMLRenderer

from api.serializers import ErpXMLSerializer
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


def upload_qs_to_xml(qs, fake_request, chunk_size=1000) -> Generator[bytes]:
    renderer = XMLRenderer()
    buffer = b'<?xml version="1.0" encoding="utf-8"?>\n<root>'
    total = qs.count()

    for offset in range(0, total, chunk_size):
        batch = qs[offset : offset + chunk_size]

        data = ErpXMLSerializer(batch, many=True, context={"request": fake_request}).data
        xml_str = renderer.render(data, accepted_media_type="application/xml", renderer_context={})
        if isinstance(xml_str, str):
            xml_str = xml_str.encode("utf-8")

        inner = re.search(rb"<root>(.*)</root>", xml_str, re.DOTALL)
        if inner:
            buffer += inner.group(1)

        if len(buffer) >= 5 * 1024 * 1024:
            yield buffer
            buffer = b""

    yield buffer + b"</root>"


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
    return True
