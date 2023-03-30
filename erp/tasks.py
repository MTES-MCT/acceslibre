from datetime import datetime, timedelta

from celery import shared_task

from core.mailer import SendInBlueMailer
from erp.models import Accessibilite, ActivitySuggestion
from erp.schema import FIELDS


@shared_task()
def compute_access_completion_rate(accessibilite_pk):
    try:
        access = Accessibilite.objects.get(pk=accessibilite_pk)
    except Accessibilite.DoesNotExist:
        return

    root_fields = [field for field in FIELDS if FIELDS[field].get("root") is True]
    nb_fields = len(root_fields)

    nb_filled_in_fields = 0
    for attr in root_fields:
        # NOTE: we can not use bool() here, as False is a filled in info
        if getattr(access, attr) not in (None, [], ""):
            nb_filled_in_fields += 1

    access.completion_rate = nb_filled_in_fields * 100 / nb_fields
    access.save(update_fields=["completion_rate"])


@shared_task()
def check_for_activity_suggestion_spam(suggestion_pk):
    try:
        suggestion = ActivitySuggestion.objects.get(pk=suggestion_pk)
    except ActivitySuggestion.DoesNotExist:
        return

    two_days_ago = datetime.now() - timedelta(hours=48)
    nb_times = ActivitySuggestion.objects.filter(user=suggestion.user, created_at__gte=two_days_ago).count()
    if nb_times >= 3:
        SendInBlueMailer().send_email(
            to_list=suggestion.user.email,
            subject=None,
            template="spam_activities_suggestion",
            context={"nb_times": nb_times},
        )
        SendInBlueMailer().mail_admins(
            subject=None,
            template="spam_activities_suggestion_admin",
            context={"nb_times": nb_times, "username": suggestion.user.username, "email": suggestion.user.email},
        )
