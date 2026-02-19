from datetime import datetime, timezone

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework_xml.renderers import XMLRenderer

from api.serializers import ErpSerializer
from erp.models import Erp

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

        self.stdout.write("Serialize data...")
        qs = Erp.objects.published().select_related("user", "accessibilite", "activite")
        qs = qs.filter(activite__id__in=ACTIVITIES)
        print(qs.count())

        server_name = settings.SITE_HOST
        factory = APIRequestFactory(SERVER_NAME=server_name)
        fake_request = factory.get("/")
        fake_request = Request(fake_request)

        data = {
            "erps": ErpSerializer(qs, many=True, context={"request": fake_request}).data,
        }

        renderer = XMLRenderer()
        xml_bytes = renderer.render(
            data,
            accepted_media_type="application/xml",
            renderer_context={},
        )

        bucket_name = settings.S3_EXPORT_BUCKET_NAME
        file_name = f"export_{now}_full.xml"

        self.stdout.write(f"Upload to S3 : {bucket_name}/{file_name}")

        s3 = boto3.client(
            "s3",
            endpoint_url=settings.S3_EXPORT_BUCKET_ENDPOINT_URL,
            # NOTE: required with boto3 1.36.x
            # config=Config(request_checksum_calculation="when_required", response_checksum_validation="when_required"),
        )

        s3.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=xml_bytes,
            ContentType="application/xml",
        )

        file_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": file_name},
            ExpiresIn=604800,
        )

        self.stdout.write(self.style.SUCCESS(f"Export terminated, link available during 7 days: {file_url}"))
