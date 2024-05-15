from contextlib import nullcontext as does_not_raise

import pytest
from django.contrib.gis.geos import Point

from erp import schema
from erp.models import Accessibilite, Activite, Erp
from erp.provider.search import get_equipments
from tests.factories import AccessibiliteFactory, ErpFactory


@pytest.fixture
def erp_with_a11y(db):
    def _factory(name, **a11y_data):
        erp = Erp.objects.create(nom=name)
        if a11y_data:
            Accessibilite.objects.create(erp=erp, **a11y_data)
        else:
            # simulate the case we have a non-a11y field filled
            Accessibilite.objects.create(erp=erp, commentaire="simple commentaire")
        return erp

    return _factory


def test_ErpQuerySet_having_a11y_data_no_data(erp_with_a11y):
    erp_with_a11y("test")
    assert Erp.objects.having_a11y_data().count() == 0


def test_ErpQuerySet_having_a11y_data_boolean(erp_with_a11y):
    erp_with_a11y("test", sanitaires_presence=None)
    assert Erp.objects.having_a11y_data().count() == 0

    erp_with_a11y("test", sanitaires_presence=True)
    assert Erp.objects.having_a11y_data().count() == 1

    erp_with_a11y("test", sanitaires_presence=False)
    assert Erp.objects.having_a11y_data().count() == 2


def test_ErpQuerySet_having_a11y_data_array(erp_with_a11y):
    erp_with_a11y("test")
    assert Erp.objects.having_a11y_data().count() == 0

    erp_with_a11y("test", accueil_equipements_malentendants=[])
    assert Erp.objects.having_a11y_data().count() == 0

    erp_with_a11y(
        "test",
        accueil_equipements_malentendants=[schema.EQUIPEMENT_MALENTENDANT_LPC],
    )
    assert Erp.objects.having_a11y_data().count() == 1


def test_ErpQuerySet_having_a11y_data_string(erp_with_a11y):
    erp_with_a11y("test", transport_information="")
    assert Erp.objects.having_a11y_data().count() == 0

    erp_with_a11y("test", transport_information="coucou")
    assert Erp.objects.having_a11y_data().count() == 1


def test_ErpQuerySet_having_a11y_data_number(erp_with_a11y):
    erp_with_a11y("test", entree_marches=0)
    assert Erp.objects.having_a11y_data().count() == 1

    erp_with_a11y("test", entree_marches=1)
    assert Erp.objects.having_a11y_data().count() == 2


def test_ErpQuerySet_having_a11y_data_accumulation(erp_with_a11y):
    erp_with_a11y("test1", accueil_retrecissement=True)
    assert Erp.objects.having_a11y_data().count() == 1

    erp_with_a11y("test2", sanitaires_presence=True)
    assert Erp.objects.having_a11y_data().count() == 2

    erp_with_a11y("test3")
    qs = Erp.objects.having_a11y_data()
    assert qs.count() == 2
    assert "test3" not in [e["nom"] for e in qs.values("nom")]


@pytest.fixture
def erp_with_geom(db):
    def _factory(name, lat, lon):
        return Erp.objects.create(nom=name, geom=Point(x=lon, y=lat, srid=4326))

    return _factory


@pytest.fixture
def paris_point():
    return Point(x=2.352222, y=48.856613, srid=4326)


@pytest.fixture
def vendargues_point():
    return Point(x=3.969950, y=43.656880, srid=4326)


@pytest.fixture
def jacou_erp(erp_with_geom):
    return erp_with_geom("e1", 43.661060, 3.912700)


def test_ErpQuerySet_nearest_point(jacou_erp, paris_point, vendargues_point):
    assert Erp.objects.nearest(paris_point, max_radius_km=1).count() == 0
    assert Erp.objects.nearest(paris_point, max_radius_km=1000).count() == 1
    assert Erp.objects.nearest(paris_point, max_radius_km=1000).first() == jacou_erp

    assert Erp.objects.nearest(vendargues_point, max_radius_km=5).count() == 1
    assert Erp.objects.nearest(vendargues_point, max_radius_km=5).first() == jacou_erp


def test_ErpQuerySet_find_duplicate(data):
    other_activity = Activite.objects.create(nom="Garage")

    erp = data.erp
    assert (
        Erp.objects.find_duplicate(
            numero=erp.numero,
            commune=erp.commune,
            activite=data.boulangerie,
            voie=erp.voie,
        ).exists()
        is True
    )

    assert (
        Erp.objects.find_duplicate(
            numero=int(erp.numero) + 1,
            commune=erp.commune,
            activite=data.boulangerie,
            voie=erp.voie,
        ).exists()
        is False
    )

    assert (
        Erp.objects.find_duplicate(
            numero=erp.numero,
            commune=erp.commune,
            activite=other_activity,
            voie=erp.voie,
        ).exists()
        is False
    )


@pytest.mark.django_db
class TestErpQuerySetFilters:
    @pytest.mark.parametrize(
        "access_attrs, should_be_returned",
        (
            pytest.param(
                {"stationnement_pmr": True, "stationnement_ext_pmr": True},
                True,
                id="nominal",
            ),
            pytest.param(
                {"stationnement_pmr": True, "stationnement_ext_pmr": False},
                True,
                id="one_false",
            ),
            pytest.param(
                {"stationnement_pmr": False, "stationnement_ext_pmr": False},
                False,
                id="both_false",
            ),
            pytest.param(
                {"stationnement_pmr": True, "stationnement_ext_pmr": None},
                True,
                id="one_unknown",
            ),
        ),
    )
    def test_having_adapted_parking(self, access_attrs, should_be_returned):
        access = AccessibiliteFactory(**access_attrs)
        assert list(Erp.objects.having_adapted_parking().all()) == ([access.erp] if should_be_returned else [])

    @pytest.mark.parametrize(
        "access_attrs, should_be_returned",
        (
            pytest.param(
                {"stationnement_presence": True, "stationnement_ext_presence": True},
                True,
                id="nominal",
            ),
            pytest.param(
                {"stationnement_presence": True, "stationnement_ext_presence": False},
                True,
                id="one_false",
            ),
            pytest.param(
                {"stationnement_presence": False, "stationnement_ext_presence": False},
                False,
                id="both_false",
            ),
            pytest.param(
                {"stationnement_presence": True, "stationnement_ext_presence": None},
                True,
                id="one_unknown",
            ),
        ),
    )
    def test_having_parking(self, access_attrs, should_be_returned):
        access = AccessibiliteFactory(**access_attrs)
        assert list(Erp.objects.having_parking().all()) == ([access.erp] if should_be_returned else [])

    def test_ensure_all_equipments_answering(self):
        qs = Erp.objects.all()
        for eq in get_equipments():
            with does_not_raise():
                getattr(qs, eq)().count()

    def test_having_label(self):
        assert Erp.objects.having_label().count() == 0

        ErpFactory(with_accessibilite=True, accessibilite__labels=None)
        assert Erp.objects.having_label().count() == 0

        ErpFactory(with_accessibilite=True, accessibilite__labels=[])
        assert Erp.objects.having_label().count() == 0

        ErpFactory(with_accessibilite=True, accessibilite__labels=["dpt", "mobalib"])
        assert Erp.objects.having_label().count() == 1
