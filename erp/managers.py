from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.postgres import search
from django.db import models
from django.db.models import Q
from django.db.models.aggregates import Count


class ActiviteQuerySet(models.QuerySet):
    def in_commune(self, commune):
        return self.filter(erp__commune__iexact=commune)

    def with_erp_counts(self):
        """ Note: this should come last when chained, otherwise you'll have
            erroneous counts.
        """
        qs = self
        qs = qs.annotate(
            count=Count(
                "erp__activite",
                filter=Q(erp__published=True, erp__geom__isnull=False),
            )
        )
        qs = qs.filter(count__gt=0)
        qs = qs.order_by("nom")
        return qs


class ErpQuerySet(models.QuerySet):
    def in_commune(self, commune):
        return self.filter(commune__iexact=commune)

    def having_activite(self, activite_slug):
        return self.filter(activite__slug=activite_slug)

    def having_an_activite(self):
        return self.filter(activite__isnull=False)

    def having_an_accessibilite(self):
        return self.filter(accessibilite__isnull=False)

    def geolocated(self):
        return self.filter(geom__isnull=False)

    def published(self):
        return self.filter(published=True)

    def autocomplete(self, query):
        qs = self.annotate(similarity=search.TrigramSimilarity("nom", query))
        qs = qs.filter(nom__trigram_similar=query)
        qs = qs.order_by("-similarity")
        return qs

    def nearest(self, coords):
        location = Point(coords[0], coords[1], srid=4326)
        return self.annotate(distance=Distance("geom", location)).order_by(
            "distance"
        )

    def search(self, query):
        qs = self.annotate(similarity=search.TrigramSimilarity("nom", query))
        qs = qs.annotate(distance=search.TrigramDistance("nom", query))
        qs = qs.annotate(
            rank=search.SearchRank(models.F("search_vector"), query)
        )
        qs = qs.filter(
            Q(search_vector=search.SearchQuery(query, config="french_unaccent"))
            | Q(nom__trigram_similar=query)
            | Q(distance__gte=0.6)
        )
        qs = qs.order_by("-rank", "-similarity", "distance")
        return qs
