# fmt: off

import pytest

from django.db import connection


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    "Installe les extensions postgres pour la suite de test pytest."
    
    with django_db_blocker.unblock(), connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
        cursor.execute("CREATE TEXT SEARCH CONFIGURATION french_unaccent( COPY = french )")
        cursor.execute("ALTER TEXT SEARCH CONFIGURATION french_unaccent ALTER MAPPING FOR hword, hword_part, word WITH unaccent, french_stem")
