import csv
import json
from dataclasses import asdict
from typing import List


def export_to_csv(file, headers, mapped_data: List):
    csv_writer = csv.DictWriter(file, fieldnames=headers)
    csv_writer.writeheader()

    for erp in mapped_data:
        data = asdict(erp)
        # TODO: better to be in dict_factory
        # Solve the quoting problem: frictionless only validate with "[""value""]",
        # but standard python lib render '["value"]'
        [
            data.update({k: json.dumps(v)})
            for k, v in data.items()
            if type(data[k]) == list
        ]
        csv_writer.writerow(data)
