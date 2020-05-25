import pytest

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point

from ..models import Activite, Commune, Erp


@pytest.fixture
def data(db):
    class Data:
        admin = User.objects.create_user(
            username="admin",
            password="Abc12345!",
            email="niko@niko.tld",
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        niko = User.objects.create_user(
            username="niko",
            password="Abc12345!",
            email="niko@niko.tld",
            is_staff=True,
            is_active=True,
        )
        sophie = User.objects.create_user(
            username="sophie",
            password="Abc12345!",
            email="sophie@sophie.tld",
            is_staff=True,
            is_active=True,
        )
        jacou = Commune.objects.create(
            nom="Jacou",
            code_postaux=["34830"],
            departement="34",
            geom=Point((3.9047933, 43.6648217)),
        )
        boulangerie = Activite.objects.create(nom="Boulangerie")
        erp = Erp.objects.create(
            nom="Aux bons croissants",
            numero="4",
            voie="grand rue",
            code_postal="34830",
            commune="Jacou",
            commune_ext=jacou,
            geom=Point((3.9047933, 43.6648217)),
            activite=boulangerie,
            published=True,
            user=niko,
        )

    return Data()
