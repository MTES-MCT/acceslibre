from pytest import mark

from erp.tasks import compute_access_completion_rate
from tests.factories import AccessibiliteFactory, ActiviteFactory, ActivitiesGroupFactory, ErpFactory


@mark.django_db
def test_compute_completion_rate():
    erp = ErpFactory(activite=ActiviteFactory(slug="boulangerie"))
    access = AccessibiliteFactory(erp=erp, cheminement_ext_presence=False)

    compute_access_completion_rate(access.pk)

    access.refresh_from_db()
    assert access.completion_rate == 5

    access.cheminement_ext_presence = True
    access.save()
    compute_access_completion_rate(access.pk)

    access.refresh_from_db()
    assert access.completion_rate == 4


@mark.django_db
def test_compute_completion_rate_hosting():
    activity = ActiviteFactory(slug="hotel", nom="Hôtel")
    ActivitiesGroupFactory(activities=[activity], name="Hébergement")
    erp = ErpFactory(activite=activity)
    access = AccessibiliteFactory(erp=erp, accueil_chambre_nombre_accessibles=None)

    compute_access_completion_rate(access.pk)

    assert "accueil_chambre_nombre_accessibles" in access.get_exposed_fields()
    access.refresh_from_db()
    assert access.completion_rate == 0

    access.accueil_chambre_nombre_accessibles = 1
    access.save()

    compute_access_completion_rate(access.pk)

    access.refresh_from_db()

    assert access.completion_rate == 3


@mark.django_db
def test_compute_completion_rate_school():
    activity = ActiviteFactory(slug="ecole", nom="École")
    ActivitiesGroupFactory(activities=[activity], name="Etablissements scolaires")
    erp = ErpFactory(activite=activity)
    access = AccessibiliteFactory(erp=erp)

    compute_access_completion_rate(access.pk)
    access.refresh_from_db()

    assert "accueil_ascenseur_etage" in access.get_exposed_fields()
    # "accueil_ascenseur_etage_pmr" must not be exposed as long as "accueil_ascenseur_etage" is not truthy
    assert "accueil_ascenseur_etage_pmr" not in access.get_exposed_fields()

    print(access.get_exposed_fields())

    access.accueil_ascenseur_etage = True
    access.save()

    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 4

    # "accueil_ascenseur_etage_pmr" should now be exposed since "accueil_ascenseur_etage" is truthy
    assert "accueil_ascenseur_etage_pmr" in access.get_exposed_fields()
    access.accueil_ascenseur_etage_pmr = True

    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()

    assert access.completion_rate == 9


@mark.django_db
def test_compute_completion_rate_healthcare():
    activity = ActiviteFactory(slug="sophrologue", nom="Sophrologue")
    ActivitiesGroupFactory(activities=[activity], name="Santé")
    erp = ErpFactory(activite=activity)
    access = AccessibiliteFactory(erp=erp)

    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    exposed_fields = access.get_exposed_fields()

    assert "accueil_soignant" in exposed_fields

    # "accueil_soignant_experience" must not be exposed as long as "accueil_soignant" is not truthy
    assert "accueil_soignant_experience" not in exposed_fields

    assert "accueil_salle_consultation_accessible" in exposed_fields
    assert "accueil_consultation_domicile" in exposed_fields
    assert "accueil_prise_en_charge_patients" in exposed_fields

    access.accueil_soignant = True
    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 4

    # "accueil_soignant_experience" should now be exposed since "accueil_soignant" is truthy
    assert "accueil_soignant_experience" in access.get_exposed_fields()
    access.accueil_soignant_experience = ["visuel"]
    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 9

    access.accueil_salle_consultation_accessible = True
    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 13

    access.accueil_consultation_domicile = False

    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 18

    access.accueil_prise_en_charge_patients = ["outils_communication"]
    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 22


@mark.django_db
def test_compute_completion_rate_large_establishments():
    activity = ActiviteFactory(slug="centre-commercial", nom="Centre commercial")
    ActivitiesGroupFactory(activities=[activity], name="Grands établissements")
    erp = ErpFactory(activite=activity)
    access = AccessibiliteFactory(erp=erp)

    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    exposed_fields = access.get_exposed_fields()

    assert "accueil_ascenseur_etage" in exposed_fields
    assert "accueil_signaletique_interieure" in exposed_fields
    # "accueil_ascenseur_etage_pmr" must not be exposed as long as "accueil_ascenseur_etage" is not truthy
    assert "accueil_ascenseur_etage_pmr" not in exposed_fields

    access.accueil_ascenseur_etage = True
    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 4

    assert "accueil_ascenseur_etage_pmr" in access.get_exposed_fields()

    # "accueil_ascenseur_etage_pmr" should now be exposed since "accueil_ascenseur_etage" is truthy
    access.accueil_ascenseur_etage_pmr = True
    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 9

    access.accueil_signaletique_interieure = True
    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 13

    exposed_fields = access.get_exposed_fields()
    assert "cheminement_ext_presence" in exposed_fields
    # "cheminement_ext_signaletique_exterieure" must not be exposed as long as "cheminement_ext_presence" is not truthy
    assert "cheminement_ext_signaletique_exterieure" not in exposed_fields
    access.cheminement_ext_presence = True
    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 14

    # "cheminement_ext_signaletique_exterieure" should now be exposed since "cheminement_ext_presence" is truthy
    assert "cheminement_ext_signaletique_exterieure" in access.get_exposed_fields()
    access.cheminement_ext_signaletique_exterieure = True
    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 17
