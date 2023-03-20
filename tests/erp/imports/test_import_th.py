import pytest
from django.contrib.gis.geos import Point
from django.core.management import call_command

from erp.management.commands.import_th import Command
from erp.models import Accessibilite, Activite, Commune, Erp


@pytest.mark.django_db
def test_import_th():
    Commune.objects.create(nom="Lyon", slug="lyon", departement="69", geom=Point(0, 0))
    activite = Activite.objects.create(nom="boulangerie")
    # 1 ERP previously flagged T&H, should keep its flag
    erp_flagged_to_keep = Erp.objects.create(
        nom="Nom",
        numero="1",
        voie="grande rue",
        code_postal="69001",
        commune="Lyon",
        activite=activite,
    )
    Accessibilite(erp=erp_flagged_to_keep, labels=["th"], labels_familles_handicap=["auditif"]).save()
    # 1 ERP previously flagged T&H, should loose its flag and been deleted
    erp_flagged_to_loose = Erp.objects.create(
        nom="Nom",
        numero="2",
        voie="grande rue",
        code_postal="69002",
        commune="Lyon",
        activite=activite,
    )
    Accessibilite(erp=erp_flagged_to_loose, labels=["th", "mobalib"], labels_familles_handicap=["auditif"]).save()
    # 1 ERP not flagged, should be now flagged
    erp_newly_flagged = Erp.objects.create(
        nom="Nom",
        numero="3",
        voie="grande rue",
        code_postal="69003",
        commune="Lyon",
        activite=activite,
    )
    Accessibilite(erp=erp_newly_flagged, labels=["mobalib"], labels_familles_handicap=["auditif"]).save()
    cm = Command()
    call_command(cm, file="data/tests/import_th.csv")

    for erp in (erp_flagged_to_keep, erp_newly_flagged):
        erp.refresh_from_db()

    assert not Erp.objects.filter(pk=erp_flagged_to_loose.pk).exists()

    assert erp_flagged_to_keep.accessibilite.labels == ["th"]
    assert len(erp_flagged_to_keep.accessibilite.labels_familles_handicap) == 2
    assert set(erp_flagged_to_keep.accessibilite.labels_familles_handicap) == set(["moteur", "mental"])

    assert len(erp_newly_flagged.accessibilite.labels) == 2
    assert set(erp_newly_flagged.accessibilite.labels) == set(["th", "mobalib"])
    assert len(erp_newly_flagged.accessibilite.labels_familles_handicap) == 2
    assert set(erp_newly_flagged.accessibilite.labels_familles_handicap) == set(["moteur", "mental"])

    new_erp = Erp.objects.get(nom="Number4")
    assert new_erp.accessibilite.labels == ["th"]
    assert len(new_erp.accessibilite.labels_familles_handicap) == 4
    assert set(new_erp.accessibilite.labels_familles_handicap) == set(["auditif", "mental", "visuel", "moteur"])
