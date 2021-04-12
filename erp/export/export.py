import csv
from dataclasses import asdict


def export_data(file, headers, mapped_data):
    csv_writer = csv.DictWriter(file, fieldnames=headers)
    csv_writer.writeheader()

    for erp in mapped_data:
        csv_writer.writerow(asdict(erp))
