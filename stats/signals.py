from django.db.models.signals import post_delete
from django.dispatch import receiver

from stats.models import ChallengePlayer
from stats.tasks import manage_challenge_player_unsubscription


@receiver(post_delete, sender=ChallengePlayer)
def challenge_player_deletion(sender, instance, **kwargs):
    challenge_player_data = {
        "user_id": instance.player.pk,
        "challenge_id": instance.challenge.pk,
    }
    manage_challenge_player_unsubscription.delay(challenge_player_data)
