from celery import shared_task
from django.http import QueryDict

from erp.export.export import export_schema_to_csv
from erp.export.mappers import ExportMapper
from erp.utils import build_queryset, cleaned_search_params_as_dict


@shared_task()
def generate_csv_file(query_params):
    decoded_params = QueryDict(query_params)

    filters = cleaned_search_params_as_dict(decoded_params)
    queryset = build_queryset(filters, decoded_params).select_related("user", "accessibilite", "activite")

    file_name = "temp_export.csv"  # FIXME should upload file to a bucket

    export_schema_to_csv(file_name, erps=queryset, model=ExportMapper)
