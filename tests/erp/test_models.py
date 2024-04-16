import pytest
import reversion
from django.core.exceptions import ValidationError

from erp.exceptions import MergeException
from erp.models import Accessibilite, Activite, ActivitySuggestion, Erp
from tests.factories import AccessibiliteFactory


class TestAccessibility:
    @pytest.mark.parametrize(
        "other, expected",
        (
            pytest.param(
                {
                    "sanitaires_presence": True,
                    "sanitaires_adaptes": False,
                    "commentaire": "foo",
                    "entree_porte_presence": True,
                    "entree_reperage": True,
                },
                True,
                id="same",
            ),
            pytest.param(
                {
                    "sanitaires_presence": True,
                    "sanitaires_adaptes": True,
                    "commentaire": "foo",
                    "entree_porte_presence": True,
                    "entree_reperage": True,
                },
                False,
                id="not_the_same",
            ),
            pytest.param(
                {
                    "sanitaires_presence": True,
                    "sanitaires_adaptes": True,
                    "commentaire": "foo",
                    "entree_porte_presence": True,
                    "entree_reperage": True,
                    "stationnement_presence": True,
                },
                False,
                id="more_attrs",
            ),
            pytest.param({"sanitaires_adaptes": False}, False, id="less_attrs"),
        ),
    )
    def test_equals(self, data, other, expected):
        other = Accessibilite(**other)
        access = data.erp.accessibilite
        assert (access == other) is expected

    def test_has_data(self, data):
        acc = Accessibilite(id=1337, erp=data.erp)
        assert acc.has_data() is False

        acc = Accessibilite(id=1337, erp=data.erp, stationnement_presence=True)
        assert acc.has_data() is True


class TestErp:
    def test_clean_validates_code_postal(self, data):
        erp = Erp.objects.create(nom="x", code_postal="1234")
        with pytest.raises(ValidationError) as excinfo:
            erp.clean()
        assert "code_postal" in excinfo.value.error_dict

    def test_clean_validates_commune_ext(self, data):
        erp = Erp.objects.create(nom="x", code_postal="12345", voie="y", commune="missing")
        with pytest.raises(ValidationError) as excinfo:
            erp.clean()
        assert "commune" in excinfo.value.error_dict

        erp = Erp.objects.create(nom="x", code_postal="34830", voie="y", commune="jacou")
        erp.clean()
        assert erp.commune_ext == data.jacou

    def test_clean_validates_siret(self, data):
        data.erp.siret = "invalid siret"
        with pytest.raises(ValidationError) as excinfo:
            data.erp.clean()
        assert "siret" in excinfo.value.error_dict

        data.erp.siret = "88076068100010"
        data.erp.clean()
        assert data.erp.siret == "88076068100010"

        data.erp.siret = "880 760 681 00010"
        data.erp.clean()
        assert data.erp.siret == "88076068100010"

    def test_clean_validates_voie(self, data):
        erp = Erp.objects.create(nom="x", code_postal="12345")
        with pytest.raises(ValidationError) as excinfo:
            erp.clean()
        assert "voie" in excinfo.value.error_dict
        assert "lieu_dit" in excinfo.value.error_dict

    def test_editable_by(self, data):
        assert data.erp.editable_by(data.niko) is True
        assert data.erp.editable_by(data.sophie) is False

    def test_metadata_tags_update_key(self, data):
        erp = Erp.objects.create(nom="erp1", metadata={"keepme": 42, "tags": ["foo", "bar"]})

        erp.metadata["tags"].append("plop")
        erp.save()

        erp = Erp.objects.get(metadata__tags__contains=["plop"])  # raises if not found
        assert erp.metadata["keepme"] == 42

    def test_metadata_tags_delete_key(self, data):
        erp = Erp.objects.create(nom="erp1", metadata={"keepme": 42, "tags": ["foo", "bar"]})

        del erp.metadata["keepme"]
        erp.save()

        erp = Erp.objects.get(metadata__tags__contains=["foo"])  # raises if not found
        assert "keepme" not in erp.metadata

    def test_metadata_tags_filter(self, data):
        Erp.objects.create(nom="erp1", metadata={"tags": ["foo", "bar"]})
        Erp.objects.create(nom="erp2", metadata={"tags": ["bar", "baz"]})

        assert Erp.objects.filter(metadata__tags__contains=["foo"]).count() == 1
        assert Erp.objects.filter(metadata__tags__contains=["baz"]).count() == 1
        assert Erp.objects.filter(metadata__tags__contains=["bar"]).count() == 2

    def test_metadata_update_nested_key(self, data):
        erp = Erp.objects.create(nom="erp1", metadata={"foo": {"bar": 42}})

        erp.metadata["foo"]["bar"] = 43
        erp.save()

        Erp.objects.get(metadata__foo__bar=43)  # raises if not found

    def test_save(self, data, activite):
        # test activity change, should wipe answers to conditional questions if we change the activity group
        data.erp.activite = Activite.objects.get(nom="Hôtel")
        data.erp.save()
        assert data.erp.activite.groups.first().name == "Hébergement", "Conditions for test not met"

        access = data.erp.accessibilite
        access.accueil_chambre_numero_visible = True
        access.save()

        erp = Erp.objects.get(pk=data.erp.pk)
        erp.activite = Activite.objects.get(nom="Hôtel restaurant")
        erp.save()

        erp = Erp.objects.get(pk=data.erp.pk)
        access = erp.accessibilite
        assert (
            access.accueil_chambre_numero_visible is True
        ), "should not wipe conditional questions' answers, same group"
        assert erp.activite.nom == "Hôtel restaurant"

        erp.activite = Activite.objects.get(nom="Accessoires")
        erp.save()

        erp = Erp.objects.get(pk=data.erp.pk)

        access = erp.accessibilite
        assert access.accueil_chambre_numero_visible is None, "should wipe conditional questions' answers"
        assert erp.activite.nom == "Accessoires"

        assert erp.published
        erp.permanently_closed = True
        erp.save()

        erp.refresh_from_db()
        assert erp.published is False, "ERP should have been unpublished as it is flagged permanently closed"


@pytest.mark.usefixtures("data")
class TestActivitySuggestion:
    def test_save(self, data, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)
        mock_mail_admins = mocker.patch("core.mailer.BrevoMailer.mail_admins", return_value=True)

        assert data.erp.activite.nom != "Autre"
        activity_suggest = ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=data.erp)
        activity_suggest.mapped_activity = Activite.objects.create(nom="Bisounours")
        activity_suggest.save()

        data.erp.refresh_from_db()
        data.erp.activite.refresh_from_db()

        assert data.erp.activite.nom == "Boulangerie", "ERP should not be affected as it was not in Other activity."

        data.erp.activite = Activite.objects.get(nom="Autre")
        data.erp.save()
        activity_suggest = ActivitySuggestion.objects.create(name="Vendeur de rêves2", erp=data.erp)

        data.erp.refresh_from_db()
        data.erp.activite.refresh_from_db()
        assert data.erp.activite.nom == "Autre", "ERP should not be affected as there is not new mapped activity."

        activity_suggest.mapped_activity = Activite.objects.create(nom="Bisounours2")
        activity_suggest.save()
        assert (
            data.erp.activite.nom == "Bisounours2"
        ), "ERP should be impacted as it was in Other activity with a new mapped activity"

        mock_mail.assert_not_called()

        # spamming suggestions
        ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=data.erp, user=data.niko)
        ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=data.erp, user=data.niko)
        ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=data.erp, user=data.sophie)
        mock_mail.assert_not_called()

        ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=data.erp, user=data.niko)
        mock_mail.assert_called_once_with(
            to_list=data.niko.email, template="spam_activities_suggestion", context={"nb_times": 3}
        )
        mock_mail_admins.assert_called_once_with(
            template="spam_activities_suggestion_admin",
            context={"nb_times": 3, "username": data.niko.username, "email": data.niko.email},
        )
        ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=data.erp, user=data.niko)
        assert mock_mail.call_count == 2
        assert mock_mail_admins.call_count == 2


def test_get_global_timestamps_no_history(data):
    erp = data.erp
    global_timestamps = erp.get_global_timestamps()
    assert global_timestamps["created_at"] == global_timestamps["updated_at"]


def test_get_global_timestamps_with_history(data, django_assert_num_queries):
    erp = data.erp

    with reversion.create_revision():
        reversion.set_user(data.niko)
        accessibilite = erp.accessibilite
        accessibilite.sanitaires_presence = False
        accessibilite.transport_station_presence = True
        accessibilite.save()

    with reversion.create_revision():
        reversion.set_user(data.niko)
        accessibilite = erp.accessibilite
        accessibilite.sanitaires_presence = True
        accessibilite.transport_station_presence = False
        accessibilite.save()

    with django_assert_num_queries(1):
        global_timestamps = erp.get_global_timestamps()
    assert global_timestamps["updated_at"] > global_timestamps["created_at"]


@pytest.mark.django_db
def test_merge_take_value_from_b_object():
    a_access = AccessibiliteFactory(stationnement_presence=None)
    b_access = AccessibiliteFactory(stationnement_presence=True)

    a_erp = a_access.erp
    b_erp = b_access.erp
    a_erp.merge_accessibility_with(b_erp)

    a_erp.refresh_from_db()
    assert a_erp.accessibilite.stationnement_presence is True


@pytest.mark.django_db
def test_merge_does_not_take_nullable_value_from_b_object():
    a_access = AccessibiliteFactory(stationnement_presence=True)
    b_access = AccessibiliteFactory(stationnement_presence=None)

    a_erp = a_access.erp
    b_erp = b_access.erp
    a_erp.merge_accessibility_with(b_erp)

    a_erp.refresh_from_db()
    assert a_erp.accessibilite.stationnement_presence is True


@pytest.mark.django_db
def test_merge_respects_fields():
    a_access = AccessibiliteFactory(stationnement_presence=None, stationnement_pmr=None)
    b_access = AccessibiliteFactory(stationnement_presence=True, stationnement_pmr=True)

    a_erp = a_access.erp
    b_erp = b_access.erp
    a_erp.merge_accessibility_with(b_erp, fields=["stationnement_pmr"])

    a_erp.refresh_from_db()
    assert a_erp.accessibilite.stationnement_presence is None
    assert a_erp.accessibilite.stationnement_pmr is True


@pytest.mark.django_db
def test_merge_cant_handle_conflicting_values():
    a_access = AccessibiliteFactory(stationnement_presence=False)
    b_access = AccessibiliteFactory(stationnement_presence=True)

    a_erp = a_access.erp
    b_erp = b_access.erp
    with pytest.raises(MergeException):
        a_erp.merge_accessibility_with(b_erp)

    a_erp.refresh_from_db()
    assert a_erp.accessibilite.stationnement_presence is False


@pytest.mark.django_db
def test_get_outside_steps_direction_text():
    access = AccessibiliteFactory(cheminement_ext_nombre_marches=10, cheminement_ext_sens_marches="montant")

    assert access.get_outside_steps_direction_text() == "montantes"

    access.cheminement_ext_nombre_marches = 1
    access.save()
    assert access.get_outside_steps_direction_text() == "montante"

    access.cheminement_ext_nombre_marches = None
    access.save()
    assert access.get_outside_steps_direction_text() is None

    access.cheminement_ext_nombre_marches = 0
    access.save()
    assert access.get_outside_steps_direction_text() is None
