from datetime import datetime, timedelta

import pytest
import reversion
from django.core.management import call_command
from django.urls import reverse
from reversion.models import Revision

from erp.schema import get_nullable_bool_fields
from tests.factories import ChallengeFactory, ChallengeTeamFactory, ErpFactory, UserFactory


@pytest.fixture()
def challenge():
    players = [UserFactory(), UserFactory()]
    yesterday = datetime.now() - timedelta(days=2)
    tomorrow = datetime.now() + timedelta(days=1)
    yield ChallengeFactory(players=players, start_date=yesterday, end_date=tomorrow)


class TestChallenge:
    @pytest.mark.django_db
    def _do_access_changes(self, user, erp, nb_changes):
        if not nb_changes:
            return

        fields_to_change = get_nullable_bool_fields()[0:nb_changes]

        with reversion.create_revision():
            reversion.set_user(user)
            for field in fields_to_change:
                setattr(erp.accessibilite, field, True)

            erp.accessibilite.save()

        yesterday = datetime.now() - timedelta(days=1)
        Revision.objects.all().update(date_created=yesterday)

    @pytest.mark.django_db
    def test_nominal_case(self, challenge, client):
        erp1, erp2, erp3 = [
            ErpFactory(with_accessibilite=True),
            ErpFactory(with_accessibilite=True),
            ErpFactory(with_accessibilite=True, published=False),
        ]

        player1, player2 = challenge.players.all()

        self._do_access_changes(user=player1, erp=erp1, nb_changes=2)
        self._do_access_changes(user=player2, erp=erp2, nb_changes=3)
        self._do_access_changes(user=player1, erp=erp3, nb_changes=3)  # should not be counted as erp3 is draft

        call_command("refresh_stats")

        challenge.refresh_from_db()

        assert challenge.get_classement() == [
            {"username": player2.username, "nb_access_info_changed": 3},
            {"username": player1.username, "nb_access_info_changed": 2},
        ]
        assert not challenge.get_classement_team()

        team = ChallengeTeamFactory()

        challenge.classement = {}  # force recompute
        challenge.save()
        challenge_player = player1.inscriptions.first()
        challenge_player.team = team
        challenge_player.save()

        call_command("refresh_stats")

        challenge.refresh_from_db()
        assert challenge.get_classement_team() == [{"team": team.name, "nb_access_info_changed": 2}]
        assert not challenge.is_finished
        assert challenge.has_open_subscriptions

        client.force_login(player1)
        client.post(
            reverse("challenge-unsubscription", kwargs={"challenge_slug": challenge.slug}),
            data={"confirm": True},
            follow=True,
        )

        call_command("refresh_stats")

        challenge.refresh_from_db()
        assert challenge.get_classement() == [
            {"username": player2.username, "nb_access_info_changed": 3},
        ], "player1 is unsubscribed, he should have been removed from previously computed leaderboard"
        assert challenge.get_classement_team() == [
            {"team": team.name, "nb_access_info_changed": 2}
        ], "team leaderboard should not be impacted, business rule"

    @pytest.mark.django_db
    def test_sub_and_unsubscription(self, client):
        challenge1 = ChallengeFactory()
        # create a second challenge we will not register to
        challenge2 = ChallengeFactory()

        user = UserFactory()

        # anonymous
        response = client.post(
            reverse("challenge-inscription", kwargs={"challenge_slug": challenge1.slug}),
            data={"confirm": True},
            follow=True,
        )

        assert challenge1.players.count() == 0

        client.force_login(user)
        response = client.post(
            reverse("challenge-inscription", kwargs={"challenge_slug": challenge1.slug}),
            data={"confirm": True},
            follow=True,
        )

        assert response.status_code == 200

        assert user in challenge1.players.all()
        assert challenge1.players.count() == 1

        assert challenge2.players.count() == 0

        response = client.post(
            reverse("challenge-unsubscription", kwargs={"challenge_slug": challenge1.slug}),
            data={"confirm": True},
            follow=True,
        )

        assert challenge1.players.count() == 0
