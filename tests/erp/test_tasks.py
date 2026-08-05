from pytest import mark

from erp.tasks import compute_access_completion_rate
from tests.factories import AccessibiliteFactory, ActiviteFactory, ActivitiesGroupFactory, ErpFactory

# Roots of the "sports_equipment" conditional, always exposed for that activity group
SPORTS_EQUIPMENT_ROOT_FIELDS = (
    "stationnement_zone_depose_pmr",
    "accueil_physique",
    "accueil_aire_de_jeux",
    "accueil_tribunes",
    "accueil_tribunes_places",
    "accueil_vestiaires",
    "accueil_douches_collectives",
    "accueil_douches_individuelles",
    "accueil_casiers",
    "accueil_prestations_complementaires",
    "accueil_presence_espaces_specifiques",
)
# Only exposed once their parent is filled in with a value triggering the children
SPORTS_EQUIPMENT_CHILD_FIELDS = (
    "accueil_tribunes_localisation_places",
    "accueil_tribunes_places_avec_accompagnants",
    "accueil_vestiaires_largeur_passage",
    "accueil_douches_collectives_adaptees",
    "accueil_douches_individuelles_adaptees",
    "accueil_casiers_adaptes",
    "accueil_casiers_fermeture",
    "sanitaires_urinoirs",
    "sanitaires_largeur_porte",
    "sanitaires_sens_transfert",
)


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
    assert "accueil_prise_en_charge_patients" not in exposed_fields
    assert "accueil_soignant_experience" not in access.get_exposed_fields()

    assert "accueil_salle_consultation_accessible" in exposed_fields
    assert "accueil_consultation_domicile" in exposed_fields

    access.accueil_soignant = True
    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 5

    access.accueil_soignant_experience = ["visuel"]
    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    # Should be ignored from completion rate
    assert access.completion_rate == 5

    access.accueil_salle_consultation_accessible = True
    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 10

    access.accueil_consultation_domicile = False

    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 15

    # accueil_prise_en_charge_patients should also be excluded from completion rate
    access.accueil_prise_en_charge_patients = ["outils_communication"]
    access.save()
    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 15


def _sports_equipment_access(**kwargs):
    activity = ActiviteFactory(slug="gymnase", nom="Gymnase")
    ActivitiesGroupFactory(activities=[activity], name="Équipements sportifs")
    return AccessibiliteFactory(erp=ErpFactory(activite=activity), **kwargs)


@mark.django_db
def test_compute_completion_rate_sports_equipment_without_children():
    access = _sports_equipment_access()

    exposed_fields = access.get_exposed_fields()
    for field in SPORTS_EQUIPMENT_ROOT_FIELDS:
        assert field in exposed_fields, f"{field} should be exposed for sports equipments"
    # no parent is filled in yet, so no child is exposed
    for field in SPORTS_EQUIPMENT_CHILD_FIELDS:
        assert field not in exposed_fields, f"{field} should not be exposed without its parent"

    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 0

    # fill in every root, keeping all parents falsy so that no child gets exposed
    access.stationnement_zone_depose_pmr = True
    access.accueil_physique = "inexistant"
    access.accueil_aire_de_jeux = False
    access.accueil_tribunes = False
    access.accueil_tribunes_places = 0
    access.accueil_vestiaires = False
    access.accueil_douches_collectives = False
    access.accueil_douches_individuelles = False
    access.accueil_casiers = False
    access.accueil_prestations_complementaires = ["score_visible"]
    access.accueil_presence_espaces_specifiques = ["presence_espace_chiens_guides"]
    access.sanitaires_presence = False
    access.save()

    compute_access_completion_rate(access.pk)
    access.refresh_from_db()

    exposed_fields = access.get_exposed_fields()
    assert set(SPORTS_EQUIPMENT_ROOT_FIELDS).issubset(exposed_fields)
    assert not set(SPORTS_EQUIPMENT_CHILD_FIELDS) & exposed_fields
    assert access.completion_rate == 41


@mark.django_db
def test_compute_completion_rate_sports_equipment_with_children():
    access = _sports_equipment_access(
        accueil_tribunes=False,
        accueil_vestiaires=False,
        accueil_douches_collectives=False,
        accueil_douches_individuelles=False,
        accueil_casiers=False,
        sanitaires_presence=False,
    )

    # each child is exposed only once its own parent displays it
    exposed_fields = access.get_exposed_fields()

    for field in SPORTS_EQUIPMENT_CHILD_FIELDS:
        assert field not in exposed_fields, f"{field} should not be exposed while its parent is False"

    access.accueil_tribunes = True
    access.accueil_vestiaires = True
    access.accueil_douches_collectives = True
    access.accueil_douches_individuelles = True
    access.accueil_casiers = True
    access.sanitaires_presence = True
    access.save()

    exposed_fields = access.get_exposed_fields()

    # direct children of the truthy roots
    assert "accueil_vestiaires_largeur_passage" in exposed_fields
    assert "accueil_douches_collectives_adaptees" in exposed_fields
    assert "accueil_douches_individuelles_adaptees" in exposed_fields
    assert "accueil_casiers_adaptes" in exposed_fields
    assert "accueil_casiers_fermeture" in exposed_fields
    assert "sanitaires_urinoirs" in exposed_fields

    # children of "sanitaires_adaptes", which is not truthy yet
    assert "sanitaires_largeur_porte" not in exposed_fields
    assert "sanitaires_sens_transfert" not in exposed_fields

    # nested children of "accueil_tribunes_places", not exposed below its min value
    assert "accueil_tribunes_localisation_places" not in exposed_fields
    assert "accueil_tribunes_places_avec_accompagnants" not in exposed_fields

    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    assert access.completion_rate == 16

    access.sanitaires_adaptes = True
    access.save()

    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    exposed_fields = access.get_exposed_fields()

    assert "sanitaires_largeur_porte" in exposed_fields
    assert "sanitaires_sens_transfert" in exposed_fields
    assert access.completion_rate == 18

    access.accueil_tribunes_places = 4
    access.save()

    compute_access_completion_rate(access.pk)
    access.refresh_from_db()
    exposed_fields = access.get_exposed_fields()

    assert "accueil_tribunes_localisation_places" in exposed_fields
    assert "accueil_tribunes_places_avec_accompagnants" in exposed_fields
    assert access.completion_rate == 20

    # fill in every remaining sports equipment field
    access.stationnement_zone_depose_pmr = True
    access.accueil_physique = "sensibilise_ou_forme"
    access.accueil_aire_de_jeux = True
    access.accueil_prestations_complementaires = ["score_visible"]
    access.accueil_presence_espaces_specifiques = ["presence_espace_chiens_guides"]
    access.accueil_tribunes_localisation_places = "niveau_aire_de_jeux"
    access.accueil_tribunes_places_avec_accompagnants = 2
    access.accueil_vestiaires_largeur_passage = "superieur_a_110"
    access.accueil_douches_collectives_adaptees = True
    access.accueil_douches_individuelles_adaptees = False
    access.accueil_casiers_adaptes = True
    access.accueil_casiers_fermeture = ["serrure_avec_cle"]
    access.sanitaires_urinoirs = True
    access.sanitaires_largeur_porte = "entre_90_et_110"
    access.sanitaires_sens_transfert = "gauche_et_droite"
    access.save()

    compute_access_completion_rate(access.pk)

    access.refresh_from_db()
    exposed_fields = access.get_exposed_fields()

    assert set(SPORTS_EQUIPMENT_ROOT_FIELDS + SPORTS_EQUIPMENT_CHILD_FIELDS).issubset(exposed_fields)

    filled_in = access.get_filled_in_fields()

    for field in SPORTS_EQUIPMENT_ROOT_FIELDS + SPORTS_EQUIPMENT_CHILD_FIELDS:
        assert field in filled_in, f"{field} should count as filled in"

    assert access.completion_rate == 57


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
