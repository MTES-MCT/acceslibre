from erp import schema
from subscription.models import ErpSubscription

from .exceptions import MainERPIdentificationException, NeedsManualInspectionException, NotDuplicatesException


def find_main_erp_and_duplicates(erps):
    if len(erps) < 2 or not all([e.has_accessibilite() for e in erps]):
        raise MainERPIdentificationException

    is_human_source = [e for e in erps if e.is_human_source]
    if len(is_human_source) == 1:
        duplicates = [e for e in erps if not e.is_human_source]
        return is_human_source[0], duplicates

    created_by_business_owner = [e for e in erps if e.was_created_by_business_owner]
    if len(created_by_business_owner) == 1:
        duplicates = [e for e in erps if not e.was_created_by_business_owner]
        return created_by_business_owner[0], duplicates

    erps_by_completion = sorted(erps, key=lambda x: x.accessibilite.completion_rate, reverse=True)
    max_completion = erps_by_completion[0].accessibilite.completion_rate
    if [e.accessibilite.completion_rate for e in erps].count(max_completion) == 1:
        return erps_by_completion[0], erps_by_completion[1:]

    by_age = sorted(erps, key=lambda x: x.created_at)
    return by_age[0], by_age[1:]


def check_for_automatic_merge(erps):
    shares_same_activity = len(set([e.activite for e in erps])) == 1

    if not shares_same_activity:
        raise NeedsManualInspectionException

    shares_same_street_name = len(set([e.voie for e in erps])) == 1
    if not shares_same_street_name:
        raise NotDuplicatesException

    shares_same_house_number = len(set([e.numero for e in erps])) == 1
    only_one_erp_with_number = len([e.numero for e in erps if e.numero]) == 1
    if shares_same_house_number or only_one_erp_with_number:
        return True

    raise NeedsManualInspectionException


def _get_value_by_condition(erp_a, erp_b, condition, field_name):
    if getattr(erp_a, condition) is True and getattr(erp_b, condition) is False:
        return getattr(erp_a.accessibilite, field_name)
    if getattr(erp_a, condition) is False and getattr(erp_b, condition) is True:
        return getattr(erp_b.accessibilite, field_name)


def get_most_reliable_field_value(erp_a, erp_b, field_name):
    a_field = getattr(erp_a.accessibilite, field_name)
    b_field = getattr(erp_b.accessibilite, field_name)
    nullable = (None, [], "")

    if a_field == b_field:
        return a_field

    if a_field is not None and b_field in nullable:
        return a_field
    if b_field is not None and a_field in nullable:
        return b_field

    for condition in ("is_human_source", "was_created_by_business_owner", "was_created_by_administration"):
        value = _get_value_by_condition(erp_a, erp_b, condition, field_name)
        if value:
            return value

    if erp_a.updated_at > erp_b.updated_at:
        return a_field
    return b_field


def move_subscriptions(main_erp, duplicates):
    for erp in duplicates:
        subscriptions = ErpSubscription.objects.filter(erp=erp)
        for subscription in subscriptions:
            ErpSubscription.subscribe(main_erp, subscription.user)
            ErpSubscription.unsubscribe(erp, subscription.user)


def merge_accessibility_with(main_erp, duplicate):
    access_destination = main_erp.accessibilite

    fields = list(schema.FIELDS.keys())
    fields.remove("activite")
    needs_save = False
    for field in fields:
        field_value = get_most_reliable_field_value(main_erp, duplicate, field)
        if field_value != getattr(access_destination, field):
            setattr(access_destination, field, field_value)
            needs_save = True

    if needs_save:
        access_destination.save()
