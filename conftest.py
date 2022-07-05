import os
import pytest

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.db import connection

from erp.models import Accessibilite, Activite, Commune, Erp

TEST_PASSWORD = "Abc12345!"


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    # Vérifie qu'on emploie bien les settings de test
    assert os.environ.get("DJANGO_SETTINGS_MODULE") == "core.settings_test"

    # Installe les extensions postgres pour la suite de test pytest
    with django_db_blocker.unblock(), connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
        cursor.execute(
            "CREATE TEXT SEARCH CONFIGURATION french_unaccent( COPY = french )"
        )
        cursor.execute(
            "ALTER TEXT SEARCH CONFIGURATION french_unaccent ALTER MAPPING FOR hword, hword_part, word WITH unaccent, french_stem"
        )


@pytest.fixture
def activite_administration_publique():
    return Activite.objects.create(nom="Administration Publique")


@pytest.fixture
def activite_mairie():
    return Activite.objects.create(nom="Mairie")


@pytest.fixture
def commune_castelnau():
    return Commune.objects.create(
        nom="Castelnau-le-Lez",
        code_postaux=["34170"],
        code_insee="34057",
        departement="93",
        geom=Point(0, 0),
    )


@pytest.fixture
def commune_montpellier():
    return Commune.objects.create(
        nom="Montpellier",
        code_postaux=["34000"],
        code_insee="34172",
        departement="34",
        geom=Point(0, 0),
    )


@pytest.fixture
def commune_montreuil():
    return Commune.objects.create(
        nom="Montreuil",
        code_postaux=["93100"],
        code_insee="93048",
        departement="93",
        geom=Point(0, 0),
    )


@pytest.fixture
def data(db):
    obj_admin = User.objects.create_user(
        username="admin",
        password=TEST_PASSWORD,
        email="admin@admin.tld",
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )
    obj_niko = User.objects.create_user(
        username="niko",
        password=TEST_PASSWORD,
        email="niko@niko.tld",
        is_staff=True,
        is_active=True,
    )
    obj_julia = User.objects.create_user(
        username="julia",
        password=TEST_PASSWORD,
        email="julia@julia.tld",
        is_staff=True,
        is_active=True,
    )
    obj_sophie = User.objects.create_user(
        username="sophie",
        password=TEST_PASSWORD,
        email="sophie@sophie.tld",
        is_staff=True,
        is_active=True,
    )
    obj_samuel = User.objects.create_user(
        username="samuel",
        password=TEST_PASSWORD,
        email="samuel@samuel.tld",
        is_staff=False,
        is_active=True,
    )
    obj_jacou = Commune.objects.create(
        nom="Jacou",
        code_postaux=["34830"],
        code_insee="34120",
        departement="34",
        geom=Point((3.9047933, 43.6648217)),
    )
    obj_boulangerie = Activite.objects.create(nom="Boulangerie")
    obj_erp = Erp.objects.create(
        nom="Aux bons croissants",
        siret="52128577500016",
        numero="4",
        voie="grand rue",
        code_postal="34830",
        commune="Jacou",
        commune_ext=obj_jacou,
        geom=Point((3.9047933, 43.6648217)),
        activite=obj_boulangerie,
        published=True,
        user=obj_niko,
    )
    obj_accessibilite = Accessibilite.objects.create(
        erp=obj_erp, sanitaires_presence=True, sanitaires_adaptes=False
    )

    class Data:
        admin = obj_admin
        niko = obj_niko
        julia = obj_julia
        sophie = obj_sophie
        samuel = obj_samuel
        jacou = obj_jacou
        boulangerie = obj_boulangerie
        accessibilite = obj_accessibilite
        erp = obj_erp

    return Data()
