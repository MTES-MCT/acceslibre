# NOTE: Currently, OVH does not support LifeCycle policies per bucket;
# if this changes, this scheduled management command could be removed. See the `exports` private GitBook page.


from datetime import datetime, timedelta, timezone

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        s3 = boto3.client("s3", endpoint_url=settings.S3_EXPORT_BUCKET_ENDPOINT_URL)
        bucket_name = settings.S3_EXPORT_BUCKET_NAME
        now = datetime.now(timezone.utc)
        response = s3.list_objects_v2(Bucket=bucket_name)
        files_to_delete = []

        for obj in response.get("Contents", []):
            # NOTE: The presigned URLs are generated with a 24-hour validity duration; set it to 25 to avoid overlap.
            if obj["LastModified"] < now - timedelta(hours=25):
                files_to_delete.append({"Key": obj["Key"]})

        if files_to_delete:
            s3.delete_objects(Bucket=bucket_name, Delete={"Objects": files_to_delete})

        self.stdout.write(f"Deleted {len(files_to_delete)} files from the S3 bucket.")
