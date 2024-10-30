from celery import shared_task

from stats.models import Challenge


@shared_task
def manage_challenge_player_unsubscription(challenge_player_data):
    challenge = Challenge.objects.get(pk=challenge_player_data["challenge_id"])
    if not isinstance(challenge.classement, dict):
        return

    for key, value in challenge.classement.items():
        challenge.classement[key] = [item for item in value if item["user_id"] != challenge_player_data["user_id"]]

    challenge.save()
