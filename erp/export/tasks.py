import hashlib
import io
from datetime import datetime, timezone

import boto3
from botocore.config import Config
from celery import shared_task
from django.conf import settings
from django.http import QueryDict

from core.mailer import BrevoMailer
from erp.export.export import export_schema_to_buffer
from erp.export.mappers import ExportMapper
from erp.utils import build_queryset, cleaned_search_params_as_dict


@shared_task()
def generate_csv_file(query_params, user_email, username):
    decoded_params = QueryDict(query_params)

    filters = cleaned_search_params_as_dict(decoded_params)
    queryset = build_queryset(filters, decoded_params, with_zone=True).select_related(
        "user", "accessibilite", "activite"
    )

    csv_buffer = io.StringIO()

    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    user_email_hash = hashlib.sha256(user_email.encode()).hexdigest()[:10]

    export_schema_to_buffer(csv_buffer, erps=queryset, model=ExportMapper)

    bucket_name = settings.S3_EXPORT_BUCKET_NAME
    file_name = f"export_{now}_{user_email_hash}.csv"

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.S3_EXPORT_BUCKET_ENDPOINT_URL,
        config=Config(request_checksum_calculation="when_required", response_checksum_validation="when_required"),
    )
    s3.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue(), ContentType="text/csv")

    file_url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": bucket_name, "Key": file_name}, ExpiresIn=86400
    )
    BrevoMailer().send_email(
        to_list=user_email, template="export-results", context={"file_url": file_url, "username": username}
    )
