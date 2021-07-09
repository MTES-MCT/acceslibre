from django.contrib.gis.geos import Point


def dict_diff_keys(old, new):
    diff = []
    for key, oldval in old.items():
        newval = new.get(key)
        if newval != oldval:
            diff.append({"field": key, "old": oldval, "new": newval})
    return diff
