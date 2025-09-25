from datetime import datetime, timedelta

from celery import shared_task

from core.mailer import BrevoMailer
from erp.forms import get_contrib_forms_for_activity
from erp.models import Accessibilite, ActivitySuggestion
from erp.schema import FIELDS


@shared_task()
def compute_access_completion_rate(accessibilite_pk):
    try:
        access = Accessibilite.objects.select_related("erp__activite").get(pk=accessibilite_pk)
    except Accessibilite.DoesNotExist:
        return

    forms_for_activity = get_contrib_forms_for_activity(access.erp.activite)

    form_fields = {field for form_class in forms_for_activity for field in form_class.base_fields.keys()}

    root_fields = [field for field in form_fields if FIELDS.get(field, {}).get("root") is True]
    nb_fields = len(root_fields)

    nb_filled_in_fields = 0
    for attr in root_fields:
        # NOTE: we can not use bool() here, as False is a filled in info
        if getattr(access, attr) not in (None, [], ""):
            nb_filled_in_fields += 1

    new_value = nb_filled_in_fields * 100 / nb_fields
    if new_value != access.completion_rate:
        # Do not use access.save() here, to avoid keeping an opened transaction and infinite loop with signal
        Accessibilite.objects.filter(pk=accessibilite_pk).update(completion_rate=new_value)


@shared_task()
def check_for_activity_suggestion_spam(suggestion_pk):
    try:
        suggestion = ActivitySuggestion.objects.get(pk=suggestion_pk)
    except ActivitySuggestion.DoesNotExist:
        return

    two_days_ago = datetime.now() - timedelta(hours=48)
    nb_times = ActivitySuggestion.objects.filter(user=suggestion.user, created_at__gte=two_days_ago).count()
    if nb_times >= 3:
        BrevoMailer().send_email(
            to_list=suggestion.user.email,
            template="spam_activities_suggestion",
            context={"nb_times": nb_times},
        )
        BrevoMailer().mail_admins(
            template="spam_activities_suggestion_admin",
            context={"nb_times": nb_times, "username": suggestion.user.username, "email": suggestion.user.email},
        )
