from django.contrib.gis.geos import Point


def parse_location(point):
    if isinstance(point, Point):
        return point
    if isinstance(point, (tuple, list)):
        try:
            return Point(x=float(point[1]), y=float(point[0]), srid=4326)
        except (TypeError, ValueError) as err:
            raise RuntimeError(f"Unable to create location from point data: {err}")
    raise RuntimeError(f"Unsupported point type {type(point)}: {point}")
