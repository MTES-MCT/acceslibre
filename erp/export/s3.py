import logging
from datetime import timedelta
from itertools import groupby

import boto3
from django.conf import settings

logger = logging.getLogger(__name__)

DATAGOUV_EXPORT_PREFIX = "datagouv-exports/"


def get_s3_export_client():
    return boto3.client("s3", endpoint_url=settings.S3_EXPORT_BUCKET_ENDPOINT_URL)


def upload_csv_to_s3(local_path, s3_key, bucket_name=None):
    s3 = get_s3_export_client()
    bucket_name = bucket_name or settings.S3_EXPORT_BUCKET_NAME
    with open(local_path, "rb") as f:
        s3.put_object(Bucket=bucket_name, Key=s3_key, Body=f.read(), ContentType="text/csv")
    return s3_key


def select_datagouv_files_to_delete(objects, now):
    """
    objects: list of s3 objects (dict with at least "Key" and "LastModified")
             already filtered on the datagouv-exports/ prefix

    Business rule: keep all files older than DATAGOUV_DAILY_RETENTION_DAYS days, and
          keep only one file per month (the oldest one).
    """
    cutoff = now - timedelta(days=settings.S3_EXPORT_DATAGOUV_DAILY_RETENTION_DAYS)
    objects = sorted(objects, key=lambda o: o["LastModified"])
    old = [o for o in objects if o["LastModified"] < cutoff]

    to_delete = []
    for _, group in groupby(old, key=lambda o: (o["LastModified"].year, o["LastModified"].month)):
        group = list(group)
        to_delete.extend(group[1:])

    return [{"Key": o["Key"]} for o in to_delete]
