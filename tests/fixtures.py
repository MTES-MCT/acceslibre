import pytest

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point

from erp.models import Accessibilite, Activite, Commune, Erp


@pytest.fixture
def data(db):
    obj_admin = User.objects.create_user(
        username="admin",
        password="Abc12345!",
        email="admin@admin.tld",
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )
    obj_niko = User.objects.create_user(
        username="niko",
        password="Abc12345!",
        email="niko@niko.tld",
        is_staff=True,
        is_active=True,
    )
    obj_sophie = User.objects.create_user(
        username="sophie",
        password="Abc12345!",
        email="sophie@sophie.tld",
        is_staff=True,
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
    obj_administration_publique = Activite.objects.create(nom="Administration Publique")
    obj_mairie = Activite.objects.create(nom="Mairie")
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
        erp=obj_erp, sanitaires_presence=True, sanitaires_adaptes=2
    )

    class Data:
        admin = obj_admin
        niko = obj_niko
        sophie = obj_sophie
        jacou = obj_jacou
        boulangerie = obj_boulangerie
        administration_publique = obj_administration_publique
        accessibilite = obj_accessibilite
        mairie = obj_mairie
        erp = obj_erp

    return Data()
