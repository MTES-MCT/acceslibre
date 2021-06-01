from erp.export.export import export_schema_to_csv
from erp.export.mappers import EtalabMapper
from erp.models import Erp


def job(*args, **kwargs):
    with open("export.csv", "w", newline="") as csv_file:
        erps = Erp.objects.published().having_a11y_data()
        export_schema_to_csv(csv_file, erps, EtalabMapper)
