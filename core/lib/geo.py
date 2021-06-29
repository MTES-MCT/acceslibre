import json

from django.contrib.gis.geos import Point, MultiPolygon, Polygon, GEOSGeometry


def geojson_mpoly(geojson):
    "Convert a geojson Polygon feature to MultiPolygon."
    mpoly = GEOSGeometry(geojson if isinstance(geojson, str) else json.dumps(geojson))
    if isinstance(mpoly, MultiPolygon):
        return mpoly
    if isinstance(mpoly, Polygon):
        return MultiPolygon([mpoly])
    raise TypeError(f"{mpoly.geom_type} not acceptable for this model")


def lonlat_to_latlon(coords):
    """Tranforms a list of coordinates in lon, lat to a list of coordinates in lat, lon.

    Context: Leaflet had the brilliant idea of using the let/lon format instead of geojson
    standard lon/lat, hence why we need to often convert shapes from one system to another.
    """
    if isinstance(coords, (tuple, list)):
        return [lonlat_to_latlon(c) for c in coords][::-1]
    else:
        return coords


def parse_location(point):
    """Returns a `geos.Point` from either:
    - a `geos.Point` instance (noop)
    - a lat/lon tuple (eg. `(43.2, 2.8)` or `("43.2", "2.8")`)
    Raises `RuntimeError` when operation fails.
    """
    if isinstance(point, Point):
        return point
    if isinstance(point, (tuple, list)):
        try:
            return Point(x=float(point[1]), y=float(point[0]), srid=4326)
        except (TypeError, ValueError) as err:
            raise RuntimeError(f"Unable to create location from point data: {err}")
    raise RuntimeError(f"Unsupported point type {type(point)}: {point}")
