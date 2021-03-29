import pytest

from erp.models import Accessibilite, Erp
from erp import schema

# ErpQuerySet


def create_test_erp(name, **a11y_data):
    erp = Erp.objects.create(nom=name)
    if a11y_data:
        Accessibilite.objects.create(erp=erp, **a11y_data)
    else:
        # simulate the case we have a non-a11y field filled
        Accessibilite.objects.create(erp=erp, commentaire="simple commentaire")
    return erp


def test_ErpQuerySet_having_a11y_data_no_data(db):
    create_test_erp("test")
    assert Erp.objects.having_a11y_data().count() == 0


def test_ErpQuerySet_having_a11y_data_boolean(db):
    create_test_erp("test", sanitaires_presence=None)
    assert Erp.objects.having_a11y_data().count() == 0

    create_test_erp("test", sanitaires_presence=True)
    assert Erp.objects.having_a11y_data().count() == 1

    create_test_erp("test", sanitaires_presence=False)
    assert Erp.objects.having_a11y_data().count() == 2


def test_ErpQuerySet_having_a11y_data_array(db):
    create_test_erp("test")
    assert Erp.objects.having_a11y_data().count() == 0

    create_test_erp("test", accueil_equipements_malentendants=[])
    assert Erp.objects.having_a11y_data().count() == 0

    create_test_erp(
        "test",
        accueil_equipements_malentendants=[schema.EQUIPEMENT_MALENTENDANT_LPC],
    )
    assert Erp.objects.having_a11y_data().count() == 1


def test_ErpQuerySet_having_a11y_data_string(db):
    create_test_erp("test", transport_information="")
    assert Erp.objects.having_a11y_data().count() == 0

    create_test_erp("test", transport_information="coucou")
    assert Erp.objects.having_a11y_data().count() == 1


def test_ErpQuerySet_having_a11y_data_number(db):
    create_test_erp("test", entree_marches=0)
    assert Erp.objects.having_a11y_data().count() == 1

    create_test_erp("test", entree_marches=1)
    assert Erp.objects.having_a11y_data().count() == 2


def test_ErpQuerySet_having_a11y_data_accumulation(db):
    create_test_erp("test1", accueil_retrecissement=True)
    assert Erp.objects.having_a11y_data().count() == 1

    create_test_erp("test2", sanitaires_presence=True)
    assert Erp.objects.having_a11y_data().count() == 2

    create_test_erp("test3")
    qs = Erp.objects.having_a11y_data()
    assert qs.count() == 2
    assert "test3" not in [e["nom"] for e in qs.values("nom")]
