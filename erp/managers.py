from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.postgres import search
from django.db import models
from django.db.models import Count, Q


class ActiviteQuerySet(models.QuerySet):
    def in_commune(self, commune):
        return self.filter(erp__commune_ext=commune)

    def with_erp_counts(self):
        """ Note: this should come last when chained, otherwise you'll have
            erroneous counts.
        """
        qs = self
        qs = qs.annotate(
            count=Count(
                "erp__activite", filter=Q(erp__published=True, erp__geom__isnull=False),
            )
        )
        qs = qs.filter(count__gt=0)
        qs = qs.order_by("nom")
        return qs


class CommuneQuerySet(models.QuerySet):
    def erp_stats(self):
        return self.annotate(
            erp_count=Count("erp", filter=Q(erp__published=True), distinct=True),
            erp_access_count=Count(
                "erp",
                filter=Q(erp__accessibilite__isnull=False, erp__published=True),
                distinct=True,
            ),
        ).order_by("-erp_access_count")

    def search(self, query):
        qs = self
        terms = query.strip().split(" ")
        clauses = Q()
        for index, term in enumerate(terms):
            if term.isdigit() and len(term) == 5:
                clauses = clauses | Q(code_postaux__contains=[term])
            if len(term) > 2:
                similarity_field = f"similarity_{index}"
                qs = qs.annotate(
                    **{similarity_field: search.TrigramSimilarity("nom", term)}
                )
                clauses = (
                    clauses
                    | Q(nom__unaccent__icontains=term)
                    | Q(**{f"{similarity_field}__gte": 0.6})
                )
        return qs.filter(clauses)


class ErpQuerySet(models.QuerySet):
    def in_commune(self, commune):
        return self.filter(commune_ext=commune)

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
        # NOTE: the Point constructor wants lon, lat
        location = Point(coords[1], coords[0], srid=4326)
        return self.annotate(distance=Distance("geom", location)).order_by("distance")

    def search(self, query):
        qs = self.annotate(similarity=search.TrigramSimilarity("nom", query))
        qs = qs.annotate(distance_nom=search.TrigramDistance("nom", query))
        qs = qs.annotate(rank=search.SearchRank(models.F("search_vector"), query))

        clauses = Q()
        clauses = clauses | Q(
            search_vector=search.SearchQuery(query, config="french_unaccent")
        )
        clauses = clauses | Q(nom__trigram_similar=query) & Q(distance_nom__gte=0.6)

        qs = qs.filter(clauses).order_by("-rank", "-similarity", "distance_nom")

        return qs
