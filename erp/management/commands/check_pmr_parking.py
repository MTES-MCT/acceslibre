import requests
from django.core.management.base import BaseCommand
from tqdm import tqdm

from erp.models import Erp

# https://opendata.paris.fr/explore/dataset/stationnement-voie-publique-emplacements/api/?disjunctive.regpri&disjunctive.regpar&disjunctive.typsta&disjunctive.arrond&disjunctive.zoneres&disjunctive.locsta&disjunctive.parite&disjunctive.signhor&disjunctive.signvert&disjunctive.confsign&disjunctive.typemob&disjunctive.zoneasp&disjunctive.stv&disjunctive.prefet&refine.regpar=GIG%2FGIC+Elargie&refine.regpar=GIG%2FGIC+Standard&basemap=jawg.dark&location=12,48.85896,2.34421

# TODO maybe add more postal codes ? 93 ?
POSTAL_CODES_PREFIX = (75, 95, 78, 92, 78, 91)
BASE_URL = "https://opendata.paris.fr/api/records/1.0/search/?dataset=stationnement-voie-publique-emplacements"
FILTER_LARGE_PARKING = "&refine.regpar=GIG%2FGIC%20Elargie"
FILTER_STANDARD_PARKING = "&refine.regpar=GIG%2FGIC%20Standard"
DISTANCE_IN_METERS = 200


class Command(BaseCommand):
    def _set_pmr_parking(self, erp):
        if not erp.has_accessibilite():
            return  # TODO check with ML what to do
        # print(f"✅ Found parking spot for erp {erp}")
        accessibilite = erp.accessibilite
        accessibilite.stationnement_pmr = True
        accessibilite.save()

    def _unset_pmr_parking(self, erp):
        if not erp.has_accessibilite():
            return  # TODO check with ML what to do
        # print(f"❌ No parking spot for erp {erp}")
        accessibilite = erp.accessibilite
        accessibilite.stationnement_pmr = False
        accessibilite.save()

    def _handle_postal_code(self, postal_code):
        erps = Erp.objects.filter(code_postal__startswith=postal_code).select_related("accessibilite")
        nb_erps = erps.count()
        print(f"Found {nb_erps} ERPS to check in {postal_code} area")

        with tqdm(total=nb_erps) as tqdm_bar:
            for erp in erps:
                tqdm_bar.update(1)
                geo_filter = f"&geofilter.distance={erp.geom.coords[1]}%2C{erp.geom.coords[0]}%2C{DISTANCE_IN_METERS}"
                response = requests.get(BASE_URL + FILTER_STANDARD_PARKING + geo_filter)
                if response.status_code != 200:
                    print(response.content)

                if len(response.json()["records"]):
                    self._set_pmr_parking(erp)
                else:
                    response = requests.get(BASE_URL + FILTER_LARGE_PARKING + geo_filter)
                    if response.status_code != 200:
                        print(response.content)
                    if len(response.json()["records"]):
                        self._set_pmr_parking(erp)
                    else:
                        self._unset_pmr_parking(erp)

    def handle(self, *args, **options):
        for postal_code_to_consider in POSTAL_CODES_PREFIX:
            self._handle_postal_code(postal_code_to_consider)
