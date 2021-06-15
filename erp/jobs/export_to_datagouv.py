import requests
from django.conf import settings

from erp.export.export import export_schema_to_csv, upload_to_datagouv
from erp.export.mappers import EtalabMapper
from erp.models import Erp


def job(*args, **kwargs):
    csv_path = "acceslibre.csv"
    with open(csv_path, "w", newline="") as csv_file:
        try:
            erps = Erp.objects.published().having_a11y_data()
            export_schema_to_csv(csv_file, erps, EtalabMapper)
            if settings.DATAGOUV_API_KEY:
                upload_to_datagouv(csv_path)
                ping_mattermost()
            else:
                print("Local export successful: 'acceslibre.csv'")
        except Exception as err:
            if settings.DATAGOUV_API_KEY:
                ping_mattermost(str(err))
            raise err


def ping_mattermost(error=None):
    if not settings.MATTERMOST_HOOK:
        return
    status = error if error else "Aucune erreur rencontrée"
    requests.post(
        settings.MATTERMOST_HOOK,
        json={
            "text": f"Export vers datagouv: {status}",
        },
    )
