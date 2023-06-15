from django.conf import settings
from django.contrib.gis import measure
from django.contrib.gis.db.models.functions import Distance
from django.contrib.postgres import search
from django.db import models
from django.db.models import Count, F, Max, Q
from django.db.models.functions import Length

from core.lib import text
from erp import schema


class ActiviteQuerySet(models.QuerySet):
    def with_erp_counts(self):
        """Note: this should come last when chained, otherwise you'll have
        erroneous counts.
        """
        qs = self
        qs = qs.annotate(count=Count("erp__activite", filter=Q(erp__published=True)))
        qs = qs.filter(count__gt=0)
        qs = qs.order_by("nom")
        return qs


class CommuneQuerySet(models.QuerySet):
    def having_published_erps(self):
        return (
            self.annotate(
                erp_access_count=Count("erp", filter=Q(erp__published=True), distinct=True),
                updated_at=Max("erp__updated_at"),
            )
            .filter(erp_access_count__gt=0)
            .order_by("-updated_at")
        )

    def erp_stats(self):
        return self.annotate(
            erp_access_count=Count("erp", filter=Q(erp__published=True), distinct=True),
        ).order_by("-erp_access_count")

    def search(self, query):
        qs = self.filter(obsolete=False)
        terms = query.strip().split(" ")
        clauses = Q()
        for index, term in enumerate(terms):
            if text.contains_digits(term) and len(term) == 5:
                clauses = clauses | Q(code_postaux__contains=[term])
            if len(term) > 2:
                similarity_field = f"similarity_{index}"
                qs = qs.annotate(**{similarity_field: search.TrigramSimilarity("nom", term)})
                clauses = clauses | Q(nom__unaccent__icontains=term) | Q(**{f"{similarity_field}__gte": 0.6})
        return qs.filter(clauses)

    def search_by_nom_code_postal(self, nom, code_postal):
        return self.filter(
            obsolete=False,
            nom__unaccent__iexact=nom,
            code_postaux__contains=[code_postal],
        )

    def with_published_erp_count(self):
        return self.annotate(
            erp_access_count=Count("erp", filter=Q(erp__published=True), distinct=True),
        )


class ErpQuerySet(models.QuerySet):
    def find_duplicate(
        self,
        numero: int,
        commune: str,
        activite: "Activite",  # noqa
        voie: str = None,
        lieu_dit: str = None,
        published: bool = None,
    ):
        published = True if published is None else published
        qs = self.filter(published=published, commune__iexact=commune, numero=numero, activite__pk=activite.pk)
        if voie or lieu_dit:
            clause = Q()
            if voie:
                clause = clause | Q(voie__iexact=voie)
            if lieu_dit:
                clause = clause | Q(lieu_dit__iexact=lieu_dit)
            qs = qs.filter(clause)
        return qs

    def with_activity(self):
        return self.select_related("activite")

    def find_similar(self, nom, commune, voie=None, lieu_dit=None):
        # FIXME: might be deprecated as this is not compliant with the last definition of a duplicate.
        # Prefer `find_duplicate`
        qs = self.filter(
            published=True,
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
        if not isinstance(source, (list, set, tuple)):
            source = [source]
        return self.filter(source__in=source, source_id=source_id, **filters)

    def find_existing_matches(self, nom, geom):
        return self.nearest(geom, order_it=False).filter(
            published=True,
            nom__unaccent__lower__trigram_similar=nom,
            distance__lt=measure.Distance(m=200),
        )

    def in_code_postal(self, commune):
        return self.filter(code_postal__in=commune.code_postaux)

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

    def nearest(self, point, max_radius_km=settings.MAP_SEARCH_RADIUS_KM, order_it=True):
        """Filter Erps around a given point, which can be either a `Point` instance
        or a tuple(lat, lon)."""
        qs = self.annotate(distance=Distance("geom", point))
        if max_radius_km:
            qs = qs.filter(distance__lt=measure.Distance(km=max_radius_km))
        if not order_it:
            return qs

        return qs.order_by("distance")

    def not_published(self):
        return self.filter(published=False)

    def published(self):
        return self.filter(published=True)

    def search_commune(self, query):
        # FIXME: way too much code in common with ComuneQuerySet#search which should
        #        be factored out.
        qs = self
        terms = query.strip().split(" ")
        clauses = Q()
        for index, term in enumerate(terms):
            if text.contains_digits(term) and len(term) == 5:
                clauses = clauses | Q(
                    commune_ext__obsolete=False,
                    commune_ext__code_postaux__contains=[term],
                )
            if len(term) > 2:
                similarity_field = f"similarity_{index}"
                qs = qs.annotate(**{similarity_field: search.TrigramSimilarity("commune_ext__nom", term)})
                clauses = (
                    clauses
                    | Q(**{f"{similarity_field}__gte": 0.6})
                    | Q(
                        commune_ext__obsolete=False,
                        commune_ext__nom__unaccent__icontains=term,
                    )
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

    def with_parking(self):
        return self.filter(Q(accessibilite__stationnement_pmr=True) | Q(accessibilite__stationnement_ext_pmr=True))

    def with_accessible_path(self):
        no_path = Q(accessibilite__cheminement_ext_presence=False)
        proper_surface = Q(accessibilite__cheminement_ext_terrain_stable=True) | Q(
            accessibilite__cheminement_ext_terrain_stable__isnull=True
        )
        not_narrow = Q(accessibilite__cheminement_ext_retrecissement=False) | Q(
            accessibilite__cheminement_ext_retrecissement__isnull=True
        )
        slope = Q(accessibilite__cheminement_ext_pente_presence=False) | (
            Q(accessibilite__cheminement_ext_pente_degre_difficulte="légère")
            | Q(accessibilite__cheminement_ext_pente_degre_difficulte__isnull=True)
        )
        camber = (
            Q(accessibilite__cheminement_ext_devers="aucun")
            | Q(accessibilite__cheminement_ext_devers="léger")
            | Q(accessibilite__cheminement_ext_devers__isnull=True)
        )
        with_ramp = (
            Q(accessibilite__accueil_cheminement_ascenseur=True)
            | Q(accessibilite__accueil_cheminement_rampe="fixe")
            | Q(accessibilite__accueil_cheminement_rampe="amovible")
        )
        ground_level = Q(accessibilite__cheminement_ext_plain_pied=True) | with_ramp

        accessible_path = Q(
            proper_surface,
            not_narrow,
            slope,
            camber,
            ground_level,
            accessibilite__cheminement_ext_presence=True,
        )
        return self.filter(no_path | accessible_path)

    def with_accessible_entry(self):
        specific = Q(accessibilite__entree_pmr=True)
        with_entry = Q(accessibilite__entree_largeur_mini__gte=80) | Q(accessibilite__entree_largeur_mini__isnull=True)
        ground_level = Q(accessibilite__entree_plain_pied=True) & with_entry
        etage_ascenceur = (
            Q(
                accessibilite__entree_plain_pied=False,
                accessibilite__entree_ascenseur=True,
            )
            & with_entry
        )
        with_ramp = Q(accessibilite__accueil_cheminement_rampe="fixe") | Q(
            accessibilite__accueil_cheminement_rampe="amovible"
        )
        ramp_level = (
            Q(
                accessibilite__entree_plain_pied=False,
                accessibilite__entree_ascenseur=True,
            )
            & with_entry
            & with_ramp
        )
        return self.filter(specific | ground_level | etage_ascenceur | ramp_level)
