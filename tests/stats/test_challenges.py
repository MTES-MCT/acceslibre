from datetime import datetime, timedelta

import pytest
import reversion
from django.core.management import call_command
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
    def test_nominal_case(self, challenge):
        erp1, erp2 = [
            ErpFactory(with_accessibilite=True),
            ErpFactory(with_accessibilite=True),
        ]

        player1, player2 = challenge.players.all()

        self._do_access_changes(user=player1, erp=erp1, nb_changes=2)
        self._do_access_changes(user=player2, erp=erp2, nb_changes=3)

        call_command("refresh_stats")

        challenge.refresh_from_db()

        assert challenge.get_classement() == [
            {"username": player2.username, "nb_access_info_changed": 3},
            {"username": player1.username, "nb_access_info_changed": 2},
        ]
        assert not challenge.get_classement_team()

        team = ChallengeTeamFactory()

        player1.team = team
        player1.save()

        call_command("refresh_stats")

        challenge.refresh_from_db()
        assert not challenge.get_classement_team() == [{"team": team.name, "nb_access_info_changed": 2}]
