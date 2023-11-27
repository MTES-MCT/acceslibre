from .exceptions import MainERPIdentificationException


def find_main_erp_and_duplicates(erps):
    if len(erps) < 2 or not all([e.has_accessibilite() for e in erps]):
        raise MainERPIdentificationException

    created_by_human = [e for e in erps if e.was_created_by_human]
    if len(created_by_human) == 1:
        duplicates = [e for e in erps if not e.was_created_by_human]
        return created_by_human[0], duplicates

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


# TODO add test on me
def shares_same_data(erps):
    shares_same_activity = len(set([e.activite for e in erps])) == 1
    shares_same_address = True  # TODO waiting for more details

    return shares_same_activity and shares_same_address


def get_most_reliable_field_value(erp_a, erp_b, field_name):
    a_field = getattr(erp_a, field_name)
    b_field = getattr(erp_b, field_name)
    nullable = (None, [], "")

    if a_field == b_field:
        return a_field, False

    if a_field is not None and b_field in nullable:
        return a_field, True
    if b_field is not None and a_field in nullable:
        return b_field, True
    else:
        pass
        # TODO implement merge for fields ?
