import pytest

from erp.duplicates import find_main_erp_and_duplicates
from erp.exceptions import MainERPIdentificationException
from erp.models import Erp
from tests.factories import ErpFactory, ErpWithAccessibiliteFactory


@pytest.mark.django_db
def test_cannot_identify_main_erp_when_too_few_erps():
    with pytest.raises(MainERPIdentificationException):
        find_main_erp_and_duplicates([])

    erp = ErpWithAccessibiliteFactory()

    with pytest.raises(MainERPIdentificationException):
        find_main_erp_and_duplicates([erp])


@pytest.mark.django_db
def test_will_prefer_erp_created_by_human():
    erp_1 = ErpWithAccessibiliteFactory(source=Erp.SOURCE_SERVICE_PUBLIC)
    by_human = ErpWithAccessibiliteFactory(source=Erp.SOURCE_PUBLIC)
    erp_2 = ErpWithAccessibiliteFactory(source=Erp.SOURCE_ACCEO)
    erp_3 = ErpWithAccessibiliteFactory(source=Erp.SOURCE_SERVICE_PUBLIC)

    main, duplicates = find_main_erp_and_duplicates([erp_1, by_human, erp_2, erp_3])

    assert main == by_human
    assert duplicates == [erp_1, erp_2, erp_3]


@pytest.mark.django_db
def test_will_prefer_erp_created_by_owner_if_no_human():
    by_owner = ErpWithAccessibiliteFactory(source=Erp.SOURCE_SERVICE_PUBLIC, user_type=Erp.USER_ROLE_GESTIONNAIRE)
    erp_1 = ErpWithAccessibiliteFactory(source=Erp.SOURCE_ACCEO)
    erp_2 = ErpWithAccessibiliteFactory(source=Erp.SOURCE_SERVICE_PUBLIC)

    main, duplicates = find_main_erp_and_duplicates([erp_1, by_owner, erp_2])

    assert main == by_owner
    assert duplicates == [erp_1, erp_2]


@pytest.mark.django_db
def test_will_prefer_erp_created_by_owner_when_many_were_created_by_human():
    by_human_1 = ErpWithAccessibiliteFactory(source=Erp.SOURCE_PUBLIC)
    by_human_2 = ErpWithAccessibiliteFactory(source=Erp.SOURCE_PUBLIC)
    by_human_3 = ErpWithAccessibiliteFactory(source=Erp.SOURCE_PUBLIC)
    by_human_and_owner = ErpWithAccessibiliteFactory(source=Erp.SOURCE_PUBLIC, user_type=Erp.USER_ROLE_GESTIONNAIRE)

    main, duplicates = find_main_erp_and_duplicates([by_human_1, by_human_2, by_human_3, by_human_and_owner])

    assert main == by_human_and_owner
    assert duplicates == [by_human_1, by_human_2, by_human_3]


@pytest.mark.django_db
def test_will_prefer_erp_with_higher_completion_rate():
    by_human_and_owner_1 = ErpWithAccessibiliteFactory(
        source=Erp.SOURCE_PUBLIC, user_type=Erp.USER_ROLE_GESTIONNAIRE, accessibilite__completion_rate=1
    )
    by_human_and_owner_2 = ErpWithAccessibiliteFactory(
        source=Erp.SOURCE_PUBLIC, user_type=Erp.USER_ROLE_GESTIONNAIRE, accessibilite__completion_rate=15
    )
    by_human_and_owner_3 = ErpWithAccessibiliteFactory(
        source=Erp.SOURCE_PUBLIC, user_type=Erp.USER_ROLE_GESTIONNAIRE, accessibilite__completion_rate=75
    )

    main, duplicates = find_main_erp_and_duplicates([by_human_and_owner_3, by_human_and_owner_2, by_human_and_owner_1])

    assert main == by_human_and_owner_3
    assert duplicates == [by_human_and_owner_2, by_human_and_owner_1]


@pytest.mark.django_db
def test_will_prefer_oldest_erp():
    erp_1 = ErpWithAccessibiliteFactory(
        source=Erp.SOURCE_PUBLIC, user_type=Erp.USER_ROLE_GESTIONNAIRE, accessibilite__completion_rate=10
    )
    erp_2 = ErpWithAccessibiliteFactory(
        source=Erp.SOURCE_PUBLIC, user_type=Erp.USER_ROLE_GESTIONNAIRE, accessibilite__completion_rate=10
    )
    erp_3 = ErpWithAccessibiliteFactory(
        source=Erp.SOURCE_PUBLIC, user_type=Erp.USER_ROLE_GESTIONNAIRE, accessibilite__completion_rate=10
    )

    main, duplicates = find_main_erp_and_duplicates([erp_3, erp_2, erp_1])

    assert main == erp_1
    assert duplicates == [erp_2, erp_3]
