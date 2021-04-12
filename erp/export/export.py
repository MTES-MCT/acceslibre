import csv
from dataclasses import asdict
from typing import List


def export_to_csv(file, headers, mapped_data: List):
    csv_writer = csv.DictWriter(file, fieldnames=headers)
    csv_writer.writeheader()

    for erp in mapped_data:
        csv_writer.writerow(asdict(erp))
