from erp.export.export import export_to_csv
from erp.export.mappers import map_erp_to_json_schema
from erp.models import Erp


def job(*args, **kwargs):
    with open("export.csv", "w", newline="") as csv_file:
        erps = Erp.objects.having_a11y_data().all()
        headers, mapped_data = map_erp_to_json_schema(erps)
        export_to_csv(csv_file, headers, mapped_data)
