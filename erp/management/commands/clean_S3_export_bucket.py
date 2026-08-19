# NOTE: Currently, OVH does not support LifeCycle policies per bucket;
# if this changes, this scheduled management command could be removed. See the `exports` private GitBook page.

from datetime import datetime, timedelta, timezone

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from sentry_sdk import monitor

from erp.export.s3 import DATAGOUV_EXPORT_PREFIX, select_datagouv_files_to_delete


class Command(BaseCommand):
    help = "Clean the S3 bucket storing search results exports, XML exports for datatourisme, and datagouv CSV backups."

    @monitor(monitor_slug="clean_S3_export_bucket")
    def handle(self, *args, **kwargs):
        s3 = boto3.client("s3", endpoint_url=settings.S3_EXPORT_BUCKET_ENDPOINT_URL)
        bucket_name = settings.S3_EXPORT_BUCKET_NAME
        now = datetime.now(timezone.utc)

        response = s3.list_objects_v2(Bucket=bucket_name)
        objects = response.get("Contents", [])

        files_to_delete = []
        datagouv_objects = []

        for obj in objects:
            key = obj["Key"]
            last_modified = obj["LastModified"]
            self.stdout.write(f"Checking {key} last modified {last_modified}")

            if key.startswith(DATAGOUV_EXPORT_PREFIX):
                datagouv_objects.append(obj)
            elif key.endswith(".xml"):
                if last_modified < now - timedelta(days=8):
                    files_to_delete.append({"Key": key})
            else:
                if last_modified < now - timedelta(hours=25):
                    files_to_delete.append({"Key": key})

        files_to_delete.extend(select_datagouv_files_to_delete(datagouv_objects, now))

        if files_to_delete:
            s3.delete_objects(Bucket=bucket_name, Delete={"Objects": files_to_delete})

        self.stdout.write(f"Deleted {len(files_to_delete)} files from the S3 bucket.")
