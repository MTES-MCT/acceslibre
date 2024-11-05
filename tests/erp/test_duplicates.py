from datetime import datetime
from unittest.mock import MagicMock

import pytest

from erp.duplicates import (
    check_for_automatic_merge,
    find_main_erp_and_duplicates,
    get_most_reliable_field_value,
    move_subscriptions,
)
from erp.exceptions import MainERPIdentificationException, NeedsManualInspectionException, NotDuplicatesException
from erp.models import Erp, ExternalSource
from subscription.models import ErpSubscription
from tests.factories import ErpFactory, UserFactory


@pytest.mark.django_db
def test_cannot_identify_main_erp_when_too_few_erps():
    with pytest.raises(MainERPIdentificationException):
        find_main_erp_and_duplicates([])

    erp = ErpFactory(
        with_accessibilite=True,
    )

    with pytest.raises(MainERPIdentificationException):
        find_main_erp_and_duplicates([erp])


@pytest.mark.django_db
def test_will_prefer_erp_created_by_human():
    erp_1 = ErpFactory(with_accessibilite=True, source=ExternalSource.SOURCE_SERVICE_PUBLIC, user=None)
    by_human = ErpFactory(with_accessibilite=True, source=ExternalSource.SOURCE_PUBLIC, user=None)
    erp_2 = ErpFactory(with_accessibilite=True, source=ExternalSource.SOURCE_ACCEO, user=None)
    erp_3 = ErpFactory(with_accessibilite=True, source=ExternalSource.SOURCE_SERVICE_PUBLIC, user=None)

    main, duplicates = find_main_erp_and_duplicates([erp_1, by_human, erp_2, erp_3])

    assert main == by_human
    assert duplicates == [erp_1, erp_2, erp_3]


@pytest.mark.django_db
def test_will_prefer_erp_attributed_to__human():
    erp_1 = ErpFactory(with_accessibilite=True, source=ExternalSource.SOURCE_SERVICE_PUBLIC, user=None)
    edited_by_human = ErpFactory(with_accessibilite=True, source=ExternalSource.SOURCE_ACCEO, user=UserFactory())
    erp_2 = ErpFactory(with_accessibilite=True, source=ExternalSource.SOURCE_ACCEO, user=None)
    erp_3 = ErpFactory(with_accessibilite=True, source=ExternalSource.SOURCE_SERVICE_PUBLIC, user=None)

    main, duplicates = find_main_erp_and_duplicates([erp_1, edited_by_human, erp_2, erp_3])

    assert main == edited_by_human
    assert duplicates == [erp_1, erp_2, erp_3]


@pytest.mark.django_db
def test_will_prefer_erp_created_by_owner_if_no_human():
    by_owner = ErpFactory(
        with_accessibilite=True, source=ExternalSource.SOURCE_SERVICE_PUBLIC, user_type=Erp.USER_ROLE_GESTIONNAIRE
    )
    erp_1 = ErpFactory(with_accessibilite=True, source=ExternalSource.SOURCE_ACCEO)
    erp_2 = ErpFactory(with_accessibilite=True, source=ExternalSource.SOURCE_SERVICE_PUBLIC)

    main, duplicates = find_main_erp_and_duplicates([erp_1, by_owner, erp_2])

    assert main == by_owner
    assert duplicates == [erp_1, erp_2]


@pytest.mark.django_db
def test_will_prefer_erp_created_by_owner_when_many_were_created_by_human():
    by_human_1 = ErpFactory(with_accessibilite=True, source=ExternalSource.SOURCE_PUBLIC)
    by_human_2 = ErpFactory(with_accessibilite=True, source=ExternalSource.SOURCE_PUBLIC)
    by_human_3 = ErpFactory(with_accessibilite=True, source=ExternalSource.SOURCE_PUBLIC)
    by_human_and_owner = ErpFactory(
        with_accessibilite=True, source=ExternalSource.SOURCE_PUBLIC, user_type=Erp.USER_ROLE_GESTIONNAIRE
    )

    main, duplicates = find_main_erp_and_duplicates([by_human_1, by_human_2, by_human_3, by_human_and_owner])

    assert main == by_human_and_owner
    assert duplicates == [by_human_1, by_human_2, by_human_3]


@pytest.mark.django_db
def test_will_prefer_erp_with_higher_completion_rate():
    by_human_and_owner_1 = ErpFactory(
        with_accessibilite=True,
        source=ExternalSource.SOURCE_PUBLIC,
        user_type=Erp.USER_ROLE_GESTIONNAIRE,
        accessibilite__completion_rate=1,
    )
    by_human_and_owner_2 = ErpFactory(
        with_accessibilite=True,
        source=ExternalSource.SOURCE_PUBLIC,
        user_type=Erp.USER_ROLE_GESTIONNAIRE,
        accessibilite__completion_rate=15,
    )
    by_human_and_owner_3 = ErpFactory(
        with_accessibilite=True,
        source=ExternalSource.SOURCE_PUBLIC,
        user_type=Erp.USER_ROLE_GESTIONNAIRE,
        accessibilite__completion_rate=75,
    )

    main, duplicates = find_main_erp_and_duplicates([by_human_and_owner_3, by_human_and_owner_2, by_human_and_owner_1])

    assert main == by_human_and_owner_3
    assert duplicates == [by_human_and_owner_2, by_human_and_owner_1]


@pytest.mark.django_db
def test_will_prefer_oldest_erp():
    erp_1 = ErpFactory(
        with_accessibilite=True,
        source=ExternalSource.SOURCE_PUBLIC,
        user_type=Erp.USER_ROLE_GESTIONNAIRE,
        accessibilite__completion_rate=10,
    )
    erp_2 = ErpFactory(
        with_accessibilite=True,
        source=ExternalSource.SOURCE_PUBLIC,
        user_type=Erp.USER_ROLE_GESTIONNAIRE,
        accessibilite__completion_rate=10,
    )
    erp_3 = ErpFactory(
        with_accessibilite=True,
        source=ExternalSource.SOURCE_PUBLIC,
        user_type=Erp.USER_ROLE_GESTIONNAIRE,
        accessibilite__completion_rate=10,
    )

    main, duplicates = find_main_erp_and_duplicates([erp_3, erp_2, erp_1])

    assert main == erp_1
    assert duplicates == [erp_2, erp_3]


@pytest.mark.django_db
def test_cant_merge_two_erp_with_different_activities():
    erp_1 = ErpFactory(activite__nom="Foo")
    erp_2 = ErpFactory(activite__nom="Bar")

    with pytest.raises(NeedsManualInspectionException):
        check_for_automatic_merge([erp_1, erp_2])


@pytest.mark.django_db
def test_cant_merge_two_erp_with_different_street_name():
    erp_1 = ErpFactory(activite__nom="Foo", voie="Rue du bar")
    erp_2 = ErpFactory(activite__nom="Foo", voie="Rue du buzz")

    with pytest.raises(NotDuplicatesException):
        check_for_automatic_merge([erp_1, erp_2])


@pytest.mark.django_db
def test_can_merge_two_erp_with_same_house_number():
    erp_1 = ErpFactory(activite__nom="Foo", voie="Bar", numero=1)
    erp_2 = ErpFactory(activite__nom="Foo", voie="Bar", numero=1)

    assert check_for_automatic_merge([erp_1, erp_2]) is True


@pytest.mark.django_db
def test_can_merge_two_erp_if_one_house_number_empty():
    erp_1 = ErpFactory(activite__nom="Foo", voie="Bar", numero=1)
    erp_2 = ErpFactory(activite__nom="Foo", voie="Bar", numero=None)

    assert check_for_automatic_merge([erp_1, erp_2]) is True


@pytest.mark.django_db
def test_cant_merge_two_erp_if_two_different_house_number():
    erp_1 = ErpFactory(activite__nom="Foo", voie="Bar", numero=1)
    erp_2 = ErpFactory(activite__nom="Foo", voie="Bar", numero=100)

    with pytest.raises(NeedsManualInspectionException):
        check_for_automatic_merge([erp_1, erp_2])


@pytest.mark.django_db
def test_move_subscriptions():
    erp_1 = ErpFactory()
    erp_2 = ErpFactory()
    erp_3 = ErpFactory()

    ErpSubscription.objects.create(erp=erp_1, user=UserFactory())
    ErpSubscription.objects.create(erp=erp_2, user=UserFactory())
    ErpSubscription.objects.create(erp=erp_2, user=UserFactory())
    ErpSubscription.objects.create(erp=erp_3, user=UserFactory())

    move_subscriptions(erp_1, [erp_2, erp_3])

    assert ErpSubscription.objects.filter(erp=erp_3).count() == 0
    assert ErpSubscription.objects.filter(erp=erp_2).count() == 0
    assert ErpSubscription.objects.filter(erp=erp_1).count() == 4
    assert ErpSubscription.objects.count() == 4


@pytest.mark.django_db
def test_move_subscriptions_handles_conflict():
    erp_1 = ErpFactory()
    erp_2 = ErpFactory()
    user = UserFactory()

    ErpSubscription.objects.create(erp=erp_1, user=user)
    ErpSubscription.objects.create(erp=erp_2, user=user)

    move_subscriptions(erp_1, [erp_2])

    assert ErpSubscription.objects.filter(erp=erp_2).count() == 0
    assert ErpSubscription.objects.filter(erp=erp_1).count() == 1
    assert ErpSubscription.objects.count() == 1


@pytest.mark.parametrize(
    "a_value, b_value, expected",
    [
        (True, True, True),
        (False, False, False),
        (True, "", True),
        (None, False, False),
    ],
)
def test_merge_values_simple_case(a_value, b_value, expected):
    erp_a = MagicMock(accessibilite=MagicMock(entree_vitree=a_value))
    erp_b = MagicMock(accessibilite=MagicMock(entree_vitree=b_value))

    assert get_most_reliable_field_value(erp_a, erp_b, "entree_vitree") == expected


def test_merge_created_by_rules():
    erp_a = MagicMock(is_human_source=True, accessibilite=MagicMock(entree_vitree=True))
    erp_b = MagicMock(is_human_source=False, accessibilite=MagicMock(entree_vitree=False))
    assert get_most_reliable_field_value(erp_a, erp_b, "entree_vitree") is True

    erp_a = MagicMock(
        is_human_source=False, was_created_by_business_owner=True, accessibilite=MagicMock(entree_vitree=True)
    )
    erp_b = MagicMock(
        is_human_source=False, was_created_by_business_owner=False, accessibilite=MagicMock(entree_vitree=False)
    )
    assert get_most_reliable_field_value(erp_a, erp_b, "entree_vitree") is True

    erp_a = MagicMock(
        is_human_source=False,
        was_created_by_business_owner=False,
        was_created_by_administration=True,
        accessibilite=MagicMock(entree_vitree=True),
    )
    erp_b = MagicMock(
        is_human_source=False,
        was_created_by_business_owner=False,
        was_created_by_administration=False,
        accessibilite=MagicMock(entree_vitree=False),
    )
    assert get_most_reliable_field_value(erp_a, erp_b, "entree_vitree") is True


def test_merge_oldest_if_no_other_option():
    erp_a = MagicMock(
        is_human_source=False,
        updated_at=datetime.now(),
        was_created_by_business_owner=False,
        was_created_by_administration=False,
        accessibilite=MagicMock(entree_vitree=False),
    )
    erp_b = MagicMock(
        is_human_source=False,
        updated_at=datetime.now(),
        was_created_by_business_owner=False,
        was_created_by_administration=False,
        accessibilite=MagicMock(entree_vitree=True),
    )
    assert get_most_reliable_field_value(erp_a, erp_b, "entree_vitree") is True
