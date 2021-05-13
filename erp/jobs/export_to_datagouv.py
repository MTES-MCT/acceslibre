from erp.export.export import export_schema_to_csv
from erp.export.models import EtalabModel
from erp.models import Erp


def job(*args, **kwargs):
    with open("export.csv", "w", newline="") as csv_file:
        erps = Erp.objects.having_a11y_data().all()
        export_schema_to_csv(csv_file, erps, EtalabModel)
