import re
from datetime import datetime, timedelta, timezone

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework_xml.renderers import XMLRenderer

from api.serializers import ErpXMLSerializer
from erp.models import Erp

from .export_XML_to_s3 import ACTIVITIES, CHUNK_SIZE

FILENAME = "export.xml"


class Command(BaseCommand):
    help = "Export ERPs updated in the last 7 days in XML format to S3, for a given list of activities"

    def handle(self, *args, **options):
        since = datetime.now(timezone.utc) - timedelta(days=7)

        server_name = settings.SITE_HOST
        factory = APIRequestFactory(SERVER_NAME=server_name)
        fake_request = Request(factory.get("/"))

        qs = (
            Erp.objects.published()
            .select_related("user", "accessibilite", "activite")
            .filter(activite__id__in=ACTIVITIES)
            .filter(updated_at__gte=since)
            .order_by("id")
        )
        total = qs.count()
        self.stdout.write(f"{total} ERPs updated in the last 7 days to export...")
        if not total:
            self.stdout.write("No ERP to export")
            return

        bucket_name = settings.S3_EXPORT_PUBLIC_BUCKET_NAME

        s3 = boto3.client(
            "s3",
            endpoint_url=settings.S3_EXPORT_BUCKET_ENDPOINT_URL,
        )

        mpu = s3.create_multipart_upload(
            Bucket=bucket_name,
            Key=FILENAME,
            ContentType="application/xml",
            ACL="public-read",
        )
        upload_id = mpu["UploadId"]
        parts = []
        part_number = 1
        buffer = b'<?xml version="1.0" encoding="utf-8"?>\n<root>'
        renderer = XMLRenderer()

        try:
            for offset in range(0, total, CHUNK_SIZE):
                batch = qs[offset : offset + CHUNK_SIZE]
                self.stdout.write(f"Serialize {offset}-{offset + CHUNK_SIZE}/{total}...")

                data = ErpXMLSerializer(batch, many=True, context={"request": fake_request}).data
                xml_str = renderer.render(data, accepted_media_type="application/xml", renderer_context={})
                if isinstance(xml_str, str):
                    xml_str = xml_str.encode("utf-8")

                inner = re.search(rb"<root>(.*)</root>", xml_str, re.DOTALL)
                if inner:
                    buffer += inner.group(1)

                if len(buffer) >= 5 * 1024 * 1024:
                    self.stdout.write(f"Upload part {part_number} ({offset}-{offset + CHUNK_SIZE}/{total})...")
                    response = s3.upload_part(
                        Bucket=bucket_name,
                        Key=FILENAME,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=buffer,
                    )
                    parts.append({"PartNumber": part_number, "ETag": response["ETag"]})
                    part_number += 1
                    buffer = b""

            buffer += b"</root>"
            response = s3.upload_part(
                Bucket=bucket_name,
                Key=FILENAME,
                PartNumber=part_number,
                UploadId=upload_id,
                Body=buffer,
            )
            parts.append({"PartNumber": part_number, "ETag": response["ETag"]})

            response = s3.complete_multipart_upload(
                Bucket=bucket_name,
                Key=FILENAME,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )

        except Exception as e:
            s3.abort_multipart_upload(Bucket=bucket_name, Key=FILENAME, UploadId=upload_id)
            raise e

        bucket_public_url = settings.S3_EXPORT_BUCKET_ENDPOINT_URL.replace("https://", f"https://{bucket_name}.")

        self.stdout.write(self.style.SUCCESS(f"Export terminated: {bucket_public_url}{FILENAME}"))
