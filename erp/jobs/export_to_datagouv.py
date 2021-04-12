from erp.export.export import export_to_csv
from erp.export.mappers import map_erp_to_official_schema_v2
from erp.models import Erp, Accessibilite


def job(*args, **kwargs):
    with open('export.csv', 'w', newline='') as csv_file:
        erps = Erp.objects.select_related('accessibilite').filter(published=True)
        headers, mapped_data = map_erp_to_official_schema_v2(erps)
        export_to_csv(csv_file, headers, mapped_data)
