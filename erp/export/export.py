import csv
import json
from dataclasses import asdict
from typing import List


def factory(data):
    # Solve the quoting problem: frictionless only validate with "[""value""]",
    # but standard python lib render '["value"]'
    return dict([(x[0], json.dumps(x[1])) if type(x[1]) == list else x for x in data])


def export_to_csv(file, headers, mapped_data: List):
    csv_writer = csv.DictWriter(file, fieldnames=headers)
    csv_writer.writeheader()

    for erp in mapped_data:
        data = asdict(erp, dict_factory=factory)
        csv_writer.writerow(data)
