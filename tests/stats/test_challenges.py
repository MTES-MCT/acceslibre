from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
import reversion
from django.conf import settings
from django.core.management import call_command
from django.urls import reverse
from freezegun import freeze_time
from reversion.models import Revision

from erp.schema import get_nullable_bool_fields
from tests.factories import ChallengeFactory, ChallengeTeamFactory, ErpFactory, UserFactory

# Frozen reference time: refresh_stats windows are UTC days, without it the assertions depend on
# when the suite runs (in particular between 00:00 and 02:00).
NOW = datetime(2026, 3, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))


def paris(year, month, day, hour=0, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=ZoneInfo(settings.TIME_ZONE))


@pytest.fixture()
def challenge():
    players = [UserFactory(), UserFactory()]
    yesterday = datetime.now() - timedelta(days=2)
    tomorrow = datetime.now() + timedelta(days=1)
    yield ChallengeFactory(players=players, start_date=yesterday, end_date=tomorrow)


class TestChallenge:
    @pytest.mark.django_db
    def _do_access_changes(self, user, erp, nb_changes, date_created=None):
        if not nb_changes:
            return

        fields_to_change = get_nullable_bool_fields()[0:nb_changes]

        with reversion.create_revision():
            reversion.set_user(user)
            for field in fields_to_change:
                setattr(erp.accessibilite, field, True)

            erp.accessibilite.save()

        revisions = Revision.objects.filter(version__object_id=str(erp.accessibilite.id))
        if date_created is None:
            date_created = datetime.now() - timedelta(days=1)

        revisions.update(date_created=date_created)

    @staticmethod
    def _day_str(challenge, nb_days_diff):
        # refresh_stats works on UTC dates: the challenge has to be reloaded so the key is computed
        # on the same time basis as the one used by the command.
        challenge.refresh_from_db()
        return f"{(challenge.start_date + timedelta(days=nb_days_diff)).replace(hour=0, minute=0, second=0)}"

    @pytest.mark.django_db
    def test_nominal_case(self, challenge, client):
        erp1, erp2, erp3 = [
            ErpFactory(with_accessibility=True),
            ErpFactory(with_accessibility=True),
            ErpFactory(with_accessibility=True, published=False),
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
        assert challenge.get_classement_team() == [{"team": team.name, "nb_access_info_changed": 2}], (
            "team leaderboard should not be impacted, business rule"
        )

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

    @pytest.mark.django_db
    @freeze_time(NOW)
    def test_first_day_is_counted(self):
        # Challenge starting yesterday at 09:00 (Paris time): the contribution made yesterday at
        # 10:00 falls in the first window, which was ignored.
        player = UserFactory()
        challenge = ChallengeFactory(
            players=[player],
            start_date=paris(2026, 3, 14, 9),
            end_date=paris(2026, 3, 16, 9),
        )
        erp = ErpFactory(with_accessibility=True)

        self._do_access_changes(user=player, erp=erp, nb_changes=2, date_created=paris(2026, 3, 14, 10))

        call_command("refresh_stats")

        challenge.refresh_from_db()
        assert challenge.get_classement() == [{"username": player.username, "nb_access_info_changed": 2}]

    @pytest.mark.django_db
    @freeze_time(NOW)
    def test_contribution_before_start_date_is_not_counted(self):
        # Only contributions made after start_date count, first day included.
        player = UserFactory()
        challenge = ChallengeFactory(
            players=[player],
            start_date=paris(2026, 3, 14, 9),
            end_date=paris(2026, 3, 16, 9),
        )
        erp_before = ErpFactory(with_accessibility=True)
        erp_after = ErpFactory(with_accessibility=True)

        self._do_access_changes(user=player, erp=erp_before, nb_changes=2, date_created=paris(2026, 3, 14, 8))
        self._do_access_changes(user=player, erp=erp_after, nb_changes=3, date_created=paris(2026, 3, 14, 10))

        call_command("refresh_stats")

        challenge.refresh_from_db()
        assert challenge.get_classement() == [{"username": player.username, "nb_access_info_changed": 3}], (
            "only the contribution made after start_date should be counted"
        )

    @pytest.mark.django_db
    @freeze_time(NOW)
    def test_finished_challenge_ignores_contributions_after_end_date(self):
        # Manual refresh_stats on a finished challenge: nothing after end_date.
        player = UserFactory()
        challenge = ChallengeFactory(
            players=[player],
            start_date=paris(2026, 3, 13, 9),
            end_date=paris(2026, 3, 14, 9),
        )
        erp_inside = ErpFactory(with_accessibility=True)
        erp_after = ErpFactory(with_accessibility=True)

        self._do_access_changes(user=player, erp=erp_inside, nb_changes=2, date_created=paris(2026, 3, 13, 10))
        self._do_access_changes(user=player, erp=erp_after, nb_changes=3, date_created=paris(2026, 3, 14, 10))

        challenge.refresh_from_db()
        challenge.refresh_stats()

        challenge.refresh_from_db()
        assert challenge.is_finished
        assert challenge.get_classement() == [{"username": player.username, "nb_access_info_changed": 2}], (
            "contributions made after end_date should not be counted on a finished challenge"
        )
        assert challenge.nb_erp_total_added == 2

    @pytest.mark.django_db
    @freeze_time(NOW)
    def test_existing_days_are_not_recomputed(self):
        # A challenge already holding the days 1..N must only get the day 0 key added.
        player = UserFactory()
        challenge = ChallengeFactory(
            players=[player],
            start_date=paris(2026, 3, 14, 9),
            end_date=paris(2026, 3, 16, 9),
        )
        erp = ErpFactory(with_accessibility=True)
        self._do_access_changes(user=player, erp=erp, nb_changes=2, date_created=paris(2026, 3, 14, 10))

        day_1_str = self._day_str(challenge, 1)
        day_2_str = self._day_str(challenge, 2)
        frozen_day_1 = [{"user_id": player.id, "nb_access_info_changed": 42}]
        frozen_day_2 = [{"user_id": player.id, "nb_access_info_changed": 7}]

        challenge.classement = {day_1_str: frozen_day_1, day_2_str: frozen_day_2}
        challenge.classement_team = {day_1_str: [{"team": "Team", "nb_access_info_changed": 42}], day_2_str: []}
        challenge.save()

        challenge.refresh_stats()

        challenge.refresh_from_db()
        day_0_str = self._day_str(challenge, 0)
        assert set(challenge.classement) == {day_0_str, day_1_str, day_2_str}
        assert challenge.classement[day_1_str] == frozen_day_1
        assert challenge.classement[day_2_str] == frozen_day_2
        assert challenge.classement[day_0_str] == [{"user_id": player.id, "nb_access_info_changed": 2}]
        assert challenge.classement_team[day_1_str] == [{"team": "Team", "nb_access_info_changed": 42}]
        assert challenge.nb_erp_total_added == 51
