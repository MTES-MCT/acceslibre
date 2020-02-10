from django.views import generic
from django.contrib.gis.geos import Point
from django.shortcuts import redirect

from .models import Erp


# TODO: https://leafletjs.com/examples/geojson/
# serialize("geojson", Erp.objects.all(), geometry_field="geom", fields=("nom",))

lon = 2.352222
lat = 48.856613


class Home(generic.ListView):
    model = Erp
    queryset = Erp.objects.nearest(lon, lat)[0:10]
    template_name = "erps/index.html"


home = Home.as_view()


def to_betagouv(self):
    return redirect("https://beta.gouv.fr/startups/access4all.html")
