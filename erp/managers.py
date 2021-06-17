from django.contrib.gis import measure
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.postgres import search
from django.db import models
from django.db.models import Count, F, Max, Q
from django.db.models.functions import Length

from core.lib import text
from erp import schema


class ActiviteQuerySet(models.QuerySet):
    def in_commune(self, commune):
        return self.filter(erp__commune_ext=commune)

    def with_erp_counts(self):
        """Note: this should come last when chained, otherwise you'll have
        erroneous counts.
        """
        qs = self
        qs = qs.annotate(
            count=Count(
                "erp__activite",
                filter=Q(
                    erp__published=True,
                    erp__accessibilite__isnull=False,
                    erp__geom__isnull=False,
                ),
            )
        )
        qs = qs.filter(count__gt=0)
        qs = qs.order_by("nom")
        return qs


class CommuneQuerySet(models.QuerySet):
    def having_published_erps(self):
        return (
            self.annotate(
                erp_access_count=Count(
                    "erp",
                    filter=Q(
                        erp__accessibilite__isnull=False,
                        erp__geom__isnull=False,
                        erp__published=True,
                    ),
                    distinct=True,
                ),
                updated_at=Max("erp__updated_at"),
            )
            .filter(erp_access_count__gt=0)
            .order_by("-updated_at")
        )

    def erp_stats(self):
        return self.annotate(
            erp_access_count=Count(
                "erp",
                filter=Q(
                    erp__accessibilite__isnull=False,
                    erp__geom__isnull=False,
                    erp__published=True,
                ),
                distinct=True,
            ),
        ).order_by("-erp_access_count")

    def search(self, query):
        qs = self
        terms = query.strip().split(" ")
        clauses = Q()
        for index, term in enumerate(terms):
            if text.contains_digits(term) and len(term) == 5:
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

    def search_by_nom_code_postal(self, nom, code_postal):
        return self.filter(
            nom__unaccent__iexact=nom, code_postaux__contains=[code_postal]
        )

    def with_published_erp_count(self):
        return self.annotate(
            erp_access_count=Count(
                "erp",
                filter=Q(
                    erp__accessibilite__isnull=False,
                    erp__geom__isnull=False,
                    erp__published=True,
                ),
                distinct=True,
            ),
        )


class ErpQuerySet(models.QuerySet):
    def find_similar(self, nom, commune, voie=None, lieu_dit=None):
        qs = self.filter(
            nom__iexact=nom,
            commune__iexact=commune,
        )
        if voie or lieu_dit:
            clause = Q()
            if voie:
                clause = clause | Q(voie__iexact=voie)
            if lieu_dit:
                clause = clause | Q(lieu_dit__iexact=lieu_dit)
            qs = qs.filter(clause)
        return qs

    def find_by_source_id(self, source, source_id, **filters):
        return self.filter(source=source, source_id=source_id, **filters)

    def find_existing_matches(self, nom, geom):
        return self.nearest([geom.coords[1], geom.coords[0]]).filter(
            nom__unaccent__lower__trigram_similar=nom,
            distance__lt=measure.Distance(m=200),
        )

    def in_commune(self, commune):
        return self.filter(commune_ext=commune)

    def having_a11y_data(self):
        """Filter ERPs having at least one a11y data filled in. A11y fields are defined
        in the `erp.schema.FIELDS` dict through the `is_a11y` flag for each field."""
        qs = self
        clauses = Q()
        for field, info in schema.FIELDS.items():
            if not info["is_a11y"]:
                continue
            if info["type"] == "string":
                # Django stores blank strings instead of null values when a form is saved with
                # an empty CharField, so the db is filled with empty strings — hence this check.
                # see https://stackoverflow.com/a/34640020/330911
                qs = qs.annotate(**{f"{field}_len": Length(f"accessibilite__{field}")})
                clauses = clauses | Q(**{f"{field}_len__gt": 0})
            elif info["type"] == "array":
                # check that this arrayfield contains at least one item
                clauses = clauses | Q(**{f"accessibilite__{field}__len__gt": 0})
            elif info["nullable"] is True:
                # everything nullable is checked accordingly
                clauses = clauses | Q(**{f"accessibilite__{field}__isnull": False})
        return qs.filter(clauses)

    def having_activite(self, activite_slug):
        return self.filter(activite__slug=activite_slug)

    def having_an_activite(self):
        return self.filter(activite__isnull=False)

    def having_an_accessibilite(self):
        return self.filter(accessibilite__isnull=False)

    def geolocated(self):
        return self.filter(geom__isnull=False)

    def nearest(self, point, max_radius_km=None):
        """Filter Erps around a given point, which can be either a `Point` instance
        or a tuple(lat, lon)."""
        if isinstance(point, Point):
            location = point
        elif isinstance(point, (tuple, list)):
            location = Point(x=float(point[1]), y=float(point[0]), srid=4326)
        else:
            raise RuntimeError(f"Unsupported point type {type(point)}: {point}")
        qs = self.annotate(distance=Distance("geom", location))
        if max_radius_km:
            qs = qs.filter(distance__lt=measure.Distance(km=max_radius_km))
        return qs.order_by("distance")

    def not_published(self):
        return self.filter(
            Q(published=False) | Q(accessibilite__isnull=True) | Q(geom__isnull=True)
        )

    def published(self):
        return self.filter(published=True).geolocated().having_an_accessibilite()

    def search_commune(self, query):
        # FIXME: way too much code in common with ComuneQuerySet#search which should
        #        be factored out.
        qs = self
        terms = query.strip().split(" ")
        clauses = Q()
        for index, term in enumerate(terms):
            if text.contains_digits(term) and len(term) == 5:
                clauses = clauses | Q(commune_ext__code_postaux__contains=[term])
            if len(term) > 2:
                similarity_field = f"similarity_{index}"
                qs = qs.annotate(
                    **{
                        similarity_field: search.TrigramSimilarity(
                            "commune_ext__nom", term
                        )
                    }
                )
                clauses = (
                    clauses
                    | Q(commune_ext__nom__unaccent__icontains=term)
                    | Q(**{f"{similarity_field}__gte": 0.6})
                )
        return qs.filter(clauses)

    def search_what(self, query):
        if not query:
            return self
        return (
            self.annotate(
                rank=search.SearchRank(
                    F("search_vector"),
                    search.SearchQuery(query, config="french_unaccent"),
                )
            )
            .filter(search_vector=search.SearchQuery(query, config="french_unaccent"))
            .order_by("-rank")
        )

    def with_votes(self):
        return self.annotate(
            count_positives=Count("vote__value", filter=Q(vote__value=1)),
            count_negatives=Count("vote__value", filter=Q(vote__value=-1)),
        )
