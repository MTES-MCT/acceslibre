from rest_framework import renderers


class GeoJSONRenderer(renderers.JSONRenderer):
    media_type = "application/geo+json"
