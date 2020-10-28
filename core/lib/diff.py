from django.contrib.gis.geos import Point


def dict_diff_keys(old, new):
    diff = []
    for key, oldval in old.items():
        newval = new.get(key)
        # Convert points to tuples of float to avoid GEOS ParseException
        if isinstance(oldval, Point):
            oldval = oldval.coords
        if isinstance(newval, Point):
            newval = newval.coords
        if newval != oldval:
            diff.append({"field": key, "old": oldval, "new": newval})
    return diff
