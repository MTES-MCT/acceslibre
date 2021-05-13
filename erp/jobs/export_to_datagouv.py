from erp.export.export import export_to_csv
from erp.export.models import EtalabModel
from erp.export.utils import map_erps_to_json_schema
from erp.models import Erp


def job(*args, **kwargs):
    with open("export.csv", "w", newline="") as csv_file:
        erps = Erp.objects.having_a11y_data().all()
        headers, mapped_data = map_erps_to_json_schema(erps, EtalabModel)
        export_to_csv(csv_file, headers, mapped_data)
