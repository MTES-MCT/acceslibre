from django.contrib.gis.serializers import geojson


class ErpSerializer(geojson.Serializer):
    # see https://stackoverflow.com/a/56557206/330911

    def end_object(self, obj):
        for field in self.selected_fields:
            if field == "pk":
                continue
            elif field in self._current.keys():
                continue
            elif field == "absolute_url":
                self._current[field] = obj.get_absolute_url()
            elif field == "adresse":
                self._current[field] = obj.adresse
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
        super(ErpSerializer, self).end_object(obj)
