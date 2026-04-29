import json
from collections import defaultdict
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.core.cache import cache
from django.db.models import Avg, Case, CharField, Count, F, FloatField, Q, Value, When
from django.db.models.functions import Cast, TruncMonth
from django.utils import timezone
from django.utils.translation import gettext as translate
from reversion.models import ContentType, Version

from erp import schema
from erp.models import Accessibilite, Erp
from erp.versioning import get_previous_version


def get_active_contributors_count():
    def _query():
        return Erp.objects.published().with_user().values("user_id").distinct().count()

    return cache.get_or_set("active_contributors_count", _query, 3600)


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


def get_completion_totals(total_published_erps: int):
    def _query():
        return list(
            Accessibilite.objects.filter(erp__published=True)
            .values(
                completion_range=Case(
                    When(completion_rate__gte=0, completion_rate__lt=10, then=Value(translate("1 à 2 informations"))),
                    When(completion_rate__gte=10, completion_rate__lt=20, then=Value(translate("3 à 5 informations"))),
                    When(completion_rate__gte=20, completion_rate__lt=30, then=Value(translate("6 à 7 informations"))),
                    When(completion_rate__gte=30, completion_rate__lt=40, then=Value(translate("8 à 10 informations"))),
                    When(
                        completion_rate__gte=40, completion_rate__lt=50, then=Value(translate("10 à 11 informations"))
                    ),
                    When(
                        completion_rate__gte=50,
                        completion_rate__lte=110,
                        then=Value(translate("12 informations et plus")),
                    ),
                    output_field=CharField(),
                )
            )
            .annotate(count=Count("id"))
            .annotate(ratio=Cast(F("count"), output_field=FloatField()) * 100 / total_published_erps)
            .order_by("completion_range")
        )

    return cache.get_or_set("completion_totals", _query, 600)


def get_total_published_erps():
    def _query():
        return Erp.objects.published().count()

    return cache.get_or_set("total_published_erps", _query, 300)


def get_total_erps_per_month():
    def _query():
        now = timezone.now().date()
        six_months_ago = now.replace(day=1) - relativedelta(months=5)

        monthly = (
            Erp.objects.filter(published=True, created_at__gte=six_months_ago)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )

        total_by_month = []
        running_total = Erp.objects.filter(published=True, created_at__lt=six_months_ago).count()
        for row in monthly:
            running_total += row["total"]
            total_by_month.append({"month": row["month"], "total_erps": running_total})

        return total_by_month

    return cache.get_or_set("total_erps_per_month", _query, 300)


def get_average_completion_rate():
    def _query():
        qs = Accessibilite.objects.filter(erp__published=True).aggregate(avg_completion_rate=Avg("completion_rate"))
        return qs.get("avg_completion_rate")

    return cache.get_or_set("avg_completion_rate", _query, 600)


def get_completed_erps_from_last_12_months():
    def _query():
        now = timezone.now()
        twelve_months_ago = now - timedelta(days=365)
        total_count = get_total_published_erps()
        last_12_months_count = (
            Erp.objects.published()
            .filter(Q(created_at__gte=twelve_months_ago) | Q(updated_at__gte=twelve_months_ago))
            .count()
        )
        return (last_12_months_count / total_count * 100) if total_count else 0

    return cache.get_or_set("completed_erps_last_12_months", _query, 600)
