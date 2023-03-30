import pytest
from django.core.exceptions import ValidationError

from erp.models import Accessibilite, Activite, ActivitySuggestion, Erp, Vote


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

    def test_vote(self, data):
        assert Vote.objects.filter(erp=data.erp, user=data.niko).count() == 0

        vote = data.erp.vote(data.niko, action="DOWN")
        assert vote.value == -1
        assert Vote.objects.filter(erp=data.erp, user=data.niko).count() == 1

        # user cancels his downvote
        vote = data.erp.vote(data.niko, action="DOWN")
        assert vote is None
        assert Vote.objects.filter(erp=data.erp, user=data.niko, comment="gna").count() == 0

        # user downvote with a comment
        vote = data.erp.vote(data.niko, action="DOWN", comment="gna")
        assert vote.value == -1
        assert Vote.objects.filter(erp=data.erp, user=data.niko, comment="gna").count() == 1

        # user now upvotes
        vote = data.erp.vote(data.niko, action="UP")
        assert vote.value == 1
        assert Vote.objects.filter(erp=data.erp, user=data.niko).count() == 1

        # user cancels his previous upvote
        vote = data.erp.vote(data.niko, action="UP")
        assert vote is None
        assert Vote.objects.filter(erp=data.erp, user=data.niko).count() == 0

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


@pytest.mark.usefixtures("data")
class TestActivitySuggestion:
    def test_save(self, data, mocker):
        mock_mail = mocker.patch("core.mailer.SendInBlueMailer.send_email", return_value=True)

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

        assert mock_mail.not_called()

        # spamming suggestions
        ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=data.erp, user=data.niko)
        ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=data.erp, user=data.sophie)
        assert mock_mail.not_called()

        ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=data.erp, user=data.niko)
        assert mock_mail.called_once_with(
            subejct=None, to_list=data.niko.email, template="spam_activities_suggestion", context={"nb_times": 3}
        )
        ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=data.erp, user=data.niko)
        assert mock_mail.called_once_with(
            subejct=None, to_list=data.niko.email, template="spam_activities_suggestion", context={"nb_times": 4}
        )
