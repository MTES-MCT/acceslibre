from unittest.mock import patch

from django.test import TestCase

from stats.models import ChallengePlayer
from tests.factories import ChallengeFactory, UserFactory


class ChallengePlayerSignalTest(TestCase):
    @patch("stats.tasks.manage_challenge_player_unsubscription.delay")
    def test_challenge_player_deletion_signal(self, mock_tasks):
        challenge = ChallengeFactory()
        user = UserFactory()
        player = ChallengePlayer.objects.create(challenge=challenge, player=user)
        player.delete()

        self.assertTrue(mock_tasks.called)
        mock_tasks.assert_called_once_with({"user_id": user.pk, "challenge_id": challenge.pk})
