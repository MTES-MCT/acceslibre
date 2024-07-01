import json
from collections import defaultdict

from reversion.models import ContentType, Version

from erp import schema
from erp.models import Accessibilite, Erp
from erp.versioning import get_previous_version


def get_active_contributors_ids():
    return Erp.objects.published().with_user().values_list("user_id", flat=True).distinct("user_id").order_by("user_id")


def _get_nb_filled_in_info(access_fields):
    fields_to_count = set(schema.get_a11y_fields()) - set(schema.get_free_text_fields())
    values = [access_fields.get(f) for f in fields_to_count]
    return len([value for value in values if value not in [None, "", [], "[]"]])


def _get_score(version, previous=None):
    current_access_fields = json.loads(version.serialized_data)[0]["fields"]
    score_current = _get_nb_filled_in_info(current_access_fields)
    score_previous = 0
    if previous:
        previous_access_fields = json.loads(previous.serialized_data)[0]["fields"]
        score_previous = _get_nb_filled_in_info(previous_access_fields)

    return score_current - score_previous


def get_challenge_scores(challenge, start_date, stop_date, player_ids):

    access_content_type = ContentType.objects.get_for_model(Accessibilite)

    scores_per_user_id = defaultdict(int)
    scores_per_team_id = defaultdict(int)

    versions = (
        Version.objects.select_related("revision")
        .filter(
            content_type_id=access_content_type,
            revision__date_created__gte=start_date,
            revision__date_created__lt=stop_date,
            revision__user_id__in=player_ids,
        )
        .order_by("revision__date_created")
    )
    for version in versions.iterator():
        user_id = version.revision.user_id
        previous = get_previous_version(version)
        if not Accessibilite.objects.filter(id=version.object_id, erp__published=True).first():
            # increment score only if the erp is published
            continue
        scores_per_user_id[user_id] += _get_score(version, previous)

    for sub in challenge.inscriptions.all():
        if sub.team_id:
            scores_per_team_id[sub.team_id] += scores_per_user_id.get(sub.player_id) or 0

    return scores_per_user_id, scores_per_team_id
