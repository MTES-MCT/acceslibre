import re
from datetime import datetime, timezone

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework_xml.renderers import XMLRenderer

from api.serializers import ErpSerializer
from erp.models import Erp

CHUNK_SIZE = 1000

ACTIVITIES = [
    255,
    184,
    4,
    6,
    1,
    293,
    279,
    14,
    257,
    406,
    223,
    22,
    243,
    247,
    27,
    29,
    253,
    33,
    34,
    305,
    38,
    203,
    40,
    339,
    41,
    42,
    43,
    141,
    298,
    50,
    51,
    285,
    450,
    297,
    63,
    64,
    375,
    307,
    206,
    79,
    62,
    407,
    405,
    224,
    85,
    86,
    84,
    415,
    95,
    252,
    100,
    103,
    109,
    236,
    112,
    211,
    411,
    113,
    385,
    117,
    209,
    380,
    292,
    125,
    432,
    417,
    231,
    294,
    310,
    135,
    362,
    137,
    145,
    147,
    269,
    148,
    152,
    153,
    258,
    445,
    413,
    163,
    165,
    295,
    171,
    172,
    177,
    396,
    220,
    173,
    174,
    175,
    176,
    178,
    168,
    182,
    183,
    185,
    381,
    194,
    371,
    196,
    276,
    392,
    414,
    429,
]


class Command(BaseCommand):
    help = "Export ERP in XML format to S3"

    def handle(self, *args, **options):
        now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        server_name = settings.SITE_HOST
        factory = APIRequestFactory(SERVER_NAME=server_name)
        fake_request = Request(factory.get("/"))

        qs = (
            Erp.objects.published()
            .select_related("user", "accessibilite", "activite")
            .filter(activite__id__in=ACTIVITIES)
            .order_by("id")
        )
        total = qs.count()
        self.stdout.write(f"{total} ERPs to export...")

        bucket_name = settings.S3_EXPORT_BUCKET_NAME
        file_name = f"export_{now}_full.xml"

        s3 = boto3.client(
            "s3",
            endpoint_url=settings.S3_EXPORT_BUCKET_ENDPOINT_URL,
        )

        # Initialize the multipart upload
        mpu = s3.create_multipart_upload(Bucket=bucket_name, Key=file_name, ContentType="application/xml")
        upload_id = mpu["UploadId"]
        parts = []
        part_number = 1
        buffer = b'<?xml version="1.0" encoding="utf-8"?>\n<root>'
        renderer = XMLRenderer()

        try:
            for offset in range(0, total, CHUNK_SIZE):
                batch = qs[offset : offset + CHUNK_SIZE]
                self.stdout.write(f"Serialize {offset}-{offset + CHUNK_SIZE}/{total}...")

                data = ErpSerializer(batch, many=True, context={"request": fake_request}).data
                xml_str = renderer.render(data, accepted_media_type="application/xml", renderer_context={})
                if isinstance(xml_str, str):
                    xml_str = xml_str.encode("utf-8")

                # using ErpSerializer is serializing into <root> tag, so we need to remove it, to append it to our buffer
                inner = re.search(rb"<root>(.*)</root>", xml_str, re.DOTALL)
                if inner:
                    buffer += inner.group(1)

                # S3 multipart  requires parts >= 5MB (except the last one)
                if len(buffer) >= 5 * 1024 * 1024:
                    self.stdout.write(f"Upload part {part_number} ({offset}-{offset + CHUNK_SIZE}/{total})...")
                    response = s3.upload_part(
                        Bucket=bucket_name,
                        Key=file_name,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=buffer,
                    )
                    parts.append({"PartNumber": part_number, "ETag": response["ETag"]})
                    part_number += 1
                    buffer = b""

            # Remaining part
            buffer += "</root>".encode("utf-8")
            response = s3.upload_part(
                Bucket=bucket_name,
                Key=file_name,
                PartNumber=part_number,
                UploadId=upload_id,
                Body=buffer,
            )
            parts.append({"PartNumber": part_number, "ETag": response["ETag"]})

            s3.complete_multipart_upload(
                Bucket=bucket_name,
                Key=file_name,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )

        except Exception as e:
            s3.abort_multipart_upload(Bucket=bucket_name, Key=file_name, UploadId=upload_id)
            raise e

        file_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": file_name},
            ExpiresIn=604800,
        )

        self.stdout.write(self.style.SUCCESS(f"Export terminated, link available during 7 days: {file_url}"))
