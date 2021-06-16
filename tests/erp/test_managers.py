import pytest

from django.contrib.gis.geos import Point

from erp.models import Accessibilite, Erp
from erp import schema

# ErpQuerySet#having_a11y_data


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


# ErpQuerySet#nearest


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


def test_ErpQuerySet_nearest_tuple(jacou_erp, paris_point):
    paris_tuple = (str(paris_point[1]), str(paris_point[0]))
    assert Erp.objects.nearest(paris_tuple, max_radius_km=1).count() == 0
    assert Erp.objects.nearest(paris_tuple, max_radius_km=1000).count() == 1
    assert Erp.objects.nearest(paris_tuple, max_radius_km=1000).first() == jacou_erp
