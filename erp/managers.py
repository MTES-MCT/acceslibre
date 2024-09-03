from django.conf import settings
from django.contrib.gis import measure
from django.contrib.gis.db.models.functions import Distance
from django.contrib.postgres import search
from django.db import models
from django.db.models import Count, F, Max, Q, Case, When, IntegerField
from django.db.models.functions import Length

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
        qs = self.filter(commune__iexact=commune, activite_id=activite.pk)
        if numero is not None:
            qs = qs.filter(Q(numero=numero) | Q(numero__isnull=True))

        if published is not None:
            qs = qs.filter(published=published)

        if voie or lieu_dit:
            clause = Q()
            if voie:
                clause = clause | Q(voie__unaccent__iexact=voie)
            if lieu_dit:
                clause = clause | Q(lieu_dit__unaccent__iexact=lieu_dit)
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

    def with_municipality_first(self, municipality):
        return self.order_by(
            Case(
                When(commune__lower=municipality.lower(), then=0),
                default=1,
                output_field=IntegerField(),
            )
        )

    def with_departement_first(self, department_code):
        return self.order_by(
            Case(
                When(code_postal__startswith=department_code, then=0),
                default=1,
                output_field=IntegerField(),
            )
        )

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

    def with_user(self):
        return self.filter(user__isnull=False)

    def search_what(self, query):
        if not query:
            return self

        qs = self.annotate(similarity=search.TrigramSimilarity("nom", query))
        qs = qs.annotate(rank=search.SearchRank(F("search_vector"), query))
        qs = qs.filter(
            Q(nom__trigram_similar=query) | Q(search_vector=search.SearchQuery(query, config="french_unaccent"))
        )
        return qs.order_by("-similarity", "-rank")

    def having_adapted_parking(self):
        return self.filter(Q(accessibilite__stationnement_pmr=True) | Q(accessibilite__stationnement_ext_pmr=True))

    def having_parking(self, as_q=False):
        parking = Q(accessibilite__stationnement_presence=True) | Q(accessibilite__stationnement_ext_presence=True)
        if as_q:
            return parking
        return self.filter(parking)

    def having_public_transportation(self, as_q=False):
        public_transp = Q(accessibilite__transport_station_presence=True)
        if as_q:
            return public_transp
        return self.filter(public_transp)

    def having_no_path(self, as_q=False):
        no_path = Q(accessibilite__cheminement_ext_presence=False) | Q(
            accessibilite__cheminement_ext_presence__isnull=True
        )
        if as_q:
            return no_path
        return self.filter(no_path)

    def having_stable_ground(self, as_q=False):
        proper_surface = Q(accessibilite__cheminement_ext_terrain_stable=True) | Q(
            accessibilite__cheminement_ext_terrain_stable__isnull=True
        )
        if as_q:
            return proper_surface
        return self.filter(proper_surface)

    def having_no_shrink(self, as_q=False):
        no_shrink = Q(accessibilite__cheminement_ext_retrecissement=False) | Q(
            accessibilite__cheminement_ext_retrecissement__isnull=True
        )
        if as_q:
            return no_shrink
        return self.filter(no_shrink)

    def having_entry_no_shrink(self):
        return self.filter(
            Q(accessibilite__cheminement_ext_retrecissement=False)
            | Q(accessibilite__cheminement_ext_retrecissement__isnull=True)
        )

    def having_no_slope(self, as_q=False):
        slope = Q(accessibilite__cheminement_ext_pente_presence=False) | (
            Q(accessibilite__cheminement_ext_pente_degre_difficulte="légère")
            | Q(accessibilite__cheminement_ext_pente_degre_difficulte__isnull=True)
        )
        if as_q:
            return slope
        return self.filter(slope)

    def having_no_camber(self, as_q=False):
        camber = (
            Q(accessibilite__cheminement_ext_devers="aucun")
            | Q(accessibilite__cheminement_ext_devers="léger")
            | Q(accessibilite__cheminement_ext_devers__isnull=True)
        )
        if as_q:
            return camber
        return self.filter(camber)

    def having_accessible_exterior_path(self):
        with_ramp = (
            Q(accessibilite__cheminement_ext_ascenseur=True)
            | Q(accessibilite__cheminement_ext_rampe="fixe")
            | Q(accessibilite__cheminement_ext_rampe="amovible")
        )
        ground_level = (
            Q(accessibilite__cheminement_ext_plain_pied=True)
            | Q(accessibilite__cheminement_ext_plain_pied__isnull=True)
        ) | with_ramp

        accessible_path = Q(
            self.having_stable_ground(as_q=True),
            self.having_no_shrink(as_q=True),
            self.having_no_slope(as_q=True),
            self.having_no_camber(as_q=True),
            ground_level,
            accessibilite__cheminement_ext_presence=True,
        )
        return self.filter(self.having_no_path(as_q=True) | accessible_path)

    def having_accessible_path_to_reception(self):
        no_shrink = Q(accessibilite__accueil_retrecissement=False) | Q(
            accessibilite__accueil_retrecissement__isnull=True
        )

        with_ramp_or_elevator = (
            Q(accessibilite__accueil_cheminement_ascenseur=True)
            | Q(accessibilite__accueil_cheminement_rampe="fixe")
            | Q(accessibilite__accueil_cheminement_rampe="amovible")
        )

        ground_level_or_ramp_or_elevator = (
            Q(accessibilite__accueil_cheminement_plain_pied=True)
            | Q(accessibilite__accueil_cheminement_plain_pied__isnull=True)
        ) | with_ramp_or_elevator
        return self.filter(no_shrink & ground_level_or_ramp_or_elevator)

    def having_adapted_path(self):
        with_ramp_or_elevator = (
            Q(accessibilite__cheminement_ext_ascenseur=True)
            | Q(accessibilite__cheminement_ext_rampe="fixe")
            | Q(accessibilite__cheminement_ext_rampe="amovible")
        )
        with_stairs = Q(accessibilite__cheminement_ext_nombre_marches__gt=1) | Q(
            accessibilite__cheminement_ext_nombre_marches__isnull=True
        )
        with_stairs_and_ramp_or_elevator = with_stairs & with_ramp_or_elevator
        adapted_stairs = with_stairs_and_ramp_or_elevator | Q(accessibilite__cheminement_ext_nombre_marches__lte=1)
        ground_level = (
            Q(accessibilite__cheminement_ext_plain_pied=True)
            | Q(accessibilite__cheminement_ext_plain_pied__isnull=True)
        ) | adapted_stairs

        adapted_path = Q(
            self.having_no_slope(as_q=True),
            ground_level,
            accessibilite__cheminement_ext_presence=True,
        )
        return self.filter(self.having_no_path(as_q=True) | adapted_path)

    def having_entry_min_width(self, as_q=False):
        entry_min_width = Q(accessibilite__entree_largeur_mini__gte=80) | Q(
            accessibilite__entree_largeur_mini__isnull=True
        )
        if as_q:
            return entry_min_width
        return self.filter(entry_min_width)

    def having_accessible_entry(self):
        specific = Q(accessibilite__entree_pmr=True)
        entry_min_width = self.having_entry_min_width(as_q=True)
        ground_level = (
            Q(
                Q(accessibilite__entree_plain_pied=True) | Q(accessibilite__entree_plain_pied__isnull=True),
            )
            & entry_min_width
        )
        elevator_floor = (
            Q(
                accessibilite__entree_plain_pied=False,
                accessibilite__entree_ascenseur=True,
            )
            & entry_min_width
        )
        with_ramp = Q(accessibilite__entree_marches_rampe="fixe") | Q(accessibilite__entree_marches_rampe="amovible")
        ramp_level = (
            Q(
                accessibilite__entree_plain_pied=False,
                accessibilite__entree_ascenseur=True,
            )
            & entry_min_width
            & with_ramp
        )
        return self.filter(specific | ground_level | elevator_floor | ramp_level)

    def having_entry_low_stairs(self):
        with_ramp_or_elevator = (
            Q(accessibilite__entree_ascenseur=True)
            | Q(accessibilite__entree_marches_rampe="fixe")
            | Q(accessibilite__entree_marches_rampe="amovible")
        )
        with_stairs = Q(accessibilite__entree_marches__gt=1) | Q(accessibilite__entree_marches__isnull=True)
        with_stairs_and_ramp_or_elevator = with_stairs & with_ramp_or_elevator
        adapted_stairs = with_stairs_and_ramp_or_elevator | Q(accessibilite__entree_marches__lte=1)
        ground_level = Q(accessibilite__entree_plain_pied=True) | Q(accessibilite__entree_plain_pied__isnull=True)
        return self.filter(ground_level | adapted_stairs)

    def having_reception_low_stairs(self):
        with_ramp_or_elevator = (
            Q(accessibilite__accueil_cheminement_ascenseur=True)
            | Q(accessibilite__accueil_cheminement_rampe="fixe")
            | Q(accessibilite__accueil_cheminement_rampe="amovible")
        )
        with_stairs = Q(accessibilite__accueil_cheminement_nombre_marches__gt=1) | Q(
            accessibilite__accueil_cheminement_nombre_marches__isnull=True
        )
        with_stairs_and_ramp_or_elevator = with_stairs & with_ramp_or_elevator
        adapted_stairs = with_stairs_and_ramp_or_elevator | Q(accessibilite__accueil_cheminement_nombre_marches__lte=1)
        ground_level = Q(accessibilite__accueil_cheminement_plain_pied=True) | Q(
            accessibilite__accueil_cheminement_plain_pied__isnull=True
        )
        return self.filter(ground_level | adapted_stairs)

    def having_path_low_stairs(self):
        with_ramp_or_elevator = (
            Q(accessibilite__cheminement_ext_ascenseur=True)
            | Q(accessibilite__cheminement_ext_rampe="fixe")
            | Q(accessibilite__cheminement_ext_rampe="amovible")
        )
        with_stairs = Q(accessibilite__cheminement_ext_nombre_marches__gte=1) | Q(
            accessibilite__cheminement_ext_nombre_marches__isnull=True
        )
        with_stairs_and_ramp_or_elevator = with_stairs & with_ramp_or_elevator
        ground_level = (
            Q(accessibilite__cheminement_ext_plain_pied=True)
            | Q(accessibilite__cheminement_ext_plain_pied__isnull=True)
        ) | with_stairs_and_ramp_or_elevator

        adapted_path = Q(
            ground_level,
            accessibilite__cheminement_ext_presence=True,
        )
        return self.filter(self.having_no_path(as_q=True) | adapted_path)

    def having_staff(self):
        return self.filter(accessibilite__accueil_personnels__in=["non-formés", "formés"])

    def having_trained_staff(self):
        return self.filter(accessibilite__accueil_personnels="formés")

    def having_guide_band(self):
        return self.filter(accessibilite__cheminement_ext_bande_guidage=True)

    def having_accessible_rooms(self):
        return self.filter(accessibilite__accueil_chambre_nombre_accessibles__gte=1)

    def having_audiodescription(self):
        return self.filter(accessibilite__accueil_audiodescription_presence=True)

    def having_hearing_equipments(self):
        return self.filter(accessibilite__accueil_equipements_malentendants_presence=True)

    def having_label(self):
        return self.filter(accessibilite__labels__len__gt=0)

    def having_visible_reception(self):
        return self.filter(accessibilite__accueil_visibilite=True)

    def having_sound_beacon(self):
        return self.filter(accessibilite__entree_balise_sonore=True)

    def having_entry_call_device(self):
        return self.filter(accessibilite__entree_dispositif_appel=True)

    def having_adapted_wc(self):
        return self.filter(accessibilite__sanitaires_adaptes=True)

    def having_adapted_entry(self):
        return self.filter(accessibilite__entree_pmr=True)
