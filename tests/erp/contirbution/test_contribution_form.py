import pytest
from django.urls import reverse

from tests.factories import AccessibiliteFactory

TESTING_STEPS = [
    {
        "actual_step": 0,
        "expected_step": 1,
        "answer": "Une marche ou plus",
        "side_effects": [{"field": "entree_plain_pied", "value": False}],
        "previous_url_step": None,
    },
    {
        "actual_step": 1,
        "expected_step": 2,
        "answer": 3,
        "side_effects": [{"field": "entree_marches", "value": 3}],
        "previous_url_step": 1,
    },
    {
        "actual_step": 2,
        "expected_step": 3,
        "answer": "Monter",
        "side_effects": [{"field": "entree_marches_sens", "value": "montant"}],
        "previous_url_step": 2,
    },
    {
        "actual_step": 3,
        "expected_step": 4,
        "answer": "Rampe amovible",
        "side_effects": [{"field": "entree_marches_rampe", "value": "amovible"}],
        "previous_url_step": 3,
    },
    {
        "actual_step": 4,
        "expected_step": 7,
        "answer": "Pas de porte",
        "side_effects": [
            {"field": "entree_porte_presence", "value": False},
            {"field": "entree_porte_manoeuvre", "value": None},
        ],
        "previous_url_step": 4,
    },
]


@pytest.mark.django_db
def test_contrib_steps(django_app):
    erp = AccessibiliteFactory(entree_porte_presence=True).erp

    for step in TESTING_STEPS:
        url = reverse("contribution-step", kwargs={"erp_slug": erp.slug, "step_number": step["actual_step"]})
        response = django_app.get(url)
        assert response.status_code == 200

        form = response.forms["contribution-form"]
        form["question"] = step["answer"]

        response = form.submit()
        assert response.status_code == 302
        expected_url = reverse("contribution-step", kwargs={"erp_slug": erp.slug, "step_number": step["expected_step"]})
        assert response["Location"] == expected_url

        erp.refresh_from_db()
        access = erp.accessibilite

        for side_effect in step["side_effects"]:
            assert getattr(access, side_effect["field"]) == side_effect["value"]

        if step["previous_url_step"]:
            response = response.follow()
            previous_url = reverse(
                "contribution-step", kwargs={"erp_slug": erp.slug, "step_number": step["previous_url_step"]}
            )
            assert previous_url in response


@pytest.mark.django_db
def test_will_publish_on_last_step_if_enough_data(django_app):
    erp = AccessibiliteFactory(
        erp__published=False, entree_plain_pied=True, entree_porte_presence=True, sanitaires_presence=True
    ).erp

    url = reverse("contribution-step", kwargs={"erp_slug": erp.slug, "step_number": 12})
    response = django_app.get(url)
    assert response.status_code == 200

    form = response.forms["contribution-form"]
    form["question"] = "Non"
    response = form.submit()

    assert response.status_code == 302
    expected_url = reverse("contribution-base-success", kwargs={"erp_slug": erp.slug})
    assert response["Location"] == expected_url

    erp.refresh_from_db()
    assert erp.published is True


@pytest.mark.django_db
def test_will_not_publish_on_last_step_if_no_data(django_app):
    erp = AccessibiliteFactory(erp__published=False, entree_plain_pied=True).erp

    url = reverse("contribution-step", kwargs={"erp_slug": erp.slug, "step_number": 12})
    response = django_app.get(url)
    assert response.status_code == 200

    form = response.forms["contribution-form"]
    form["question"] = "Non"
    response = form.submit()

    assert response.status_code == 302
    expected_url = reverse("contribution-base-success", kwargs={"erp_slug": erp.slug})
    assert response["Location"] == expected_url

    erp.refresh_from_db()
    assert erp.published is False
