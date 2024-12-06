import ast
import csv

from django.core.management.base import BaseCommand

from erp.models import Erp, ExternalSource


class Command(BaseCommand):
    help = "Import RNB ids"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path of the CSV file to process (separator: ,)",
        )
        parser.add_argument("--write", action="store_true", help="Actually edit the database", default=False)

    def handle(self, *args, **options):
        self.input_file = options.get("file")
        self.should_write = options["write"]

        with open(self.input_file, "r") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",")
            for i, row in enumerate(reader):
                print(f"~ Processing line {i}")
                try:
                    erp = Erp.objects.get(uuid=row["ext_id"])
                except Erp.DoesNotExist:
                    print(f"ERP with uuid {row['ext_id']} not found. Ignoring the line...")
                    continue

                source_ids = ast.literal_eval(row["rnb_ids"])
                if not source_ids:
                    continue

                # NOTE: we have a unicity constraint on (erp, source) and cannot insert more than 1 source_id per source
                #       on a given ERP. We will manage only the first RNB_id here.
                source_id = source_ids[0]

                filters = {"source": ExternalSource.SOURCE_RNB, "source_id": source_id, "erp_id": erp.pk}
                if ExternalSource.objects.filter(**filters).exists():
                    print(f"Existing ExternalSource for ERP {erp.pk} with id {source_id}. Ignoring the source_id...")
                    continue

                qs = ExternalSource.objects.filter(erp_id=erp.pk, source=ExternalSource.SOURCE_RNB)
                if self.should_write:
                    qs.delete()
                    print(f"Deleted old source stored on ERP {erp.pk}")

                if self.should_write:
                    ExternalSource.objects.create(**filters)
                    print(f"Created ExternalSource for ERP {erp.pk} with id {source_id}")
                else:
                    print(f"Would have created ExternalSource for ERP {erp.pk} with id {source_id}")
