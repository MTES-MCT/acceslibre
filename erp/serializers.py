from django.contrib.gis.serializers import geojson


class SpecialErpSerializer(geojson.Serializer):
    # see https://stackoverflow.com/a/56557206/330911

    def end_object(self, obj):  # noqa
        for field in self.selected_fields:
            if field == "pk":
                continue
            elif field in self._current.keys():
                continue
            elif field == "absolute_url":
                self._current[field] = obj.get_absolute_url()
            elif field == "adresse":
                self._current[field] = obj.adresse
            elif field == "has_accessibilite":
                self._current[field] = obj.has_accessibilite()
            else:
                try:
                    if "__" in field:
                        fields = field.split("__")
                        value = obj
                        for f in fields:
                            value = getattr(value, f)
                        if value != obj:
                            self._current[field] = value
                except AttributeError:
                    pass
        super().end_object(obj)
