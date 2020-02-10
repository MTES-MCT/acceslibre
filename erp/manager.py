from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db import models


class ErpManager(models.Manager):
    def nearest(self, lon, lat):
        location = Point(lon, lat, srid=4326)
        return self.annotate(distance=Distance("geom", location)).order_by(
            "distance"
        )
