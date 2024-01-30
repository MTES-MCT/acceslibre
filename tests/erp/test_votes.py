from django.core import mail
from django.urls import reverse

from erp.models import Vote
from tests.utils import assert_redirect


def test_erp_cannot_vote_as_anonymous(data, client):
    response = client.post(
        reverse("erp_vote", kwargs={"erp_slug": data.erp.slug}),
        {"action": "DOWN", "comment": "bouh"},
        follow=True,
    )

    # ensure user is redirected to login page
    assert_redirect(response, "/compte/login/?next=/app/aux-bons-croissants/vote/")
    assert response.status_code == 200
    assert "registration/login.html" in [t.name for t in response.templates]


def test_erp_cannot_vote_when_user_is_owner(data, client, mocker):
    mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)

    client.force_login(data.niko)

    response = client.post(
        reverse("erp_vote", kwargs={"erp_slug": data.erp.slug}),
        {"action": "DOWN", "comment": "bouh"},
        follow=True,
    )

    assert response.status_code == 400
    mock_mail.assert_not_called()

    # Ensure votes are not counted
    assert Vote.objects.filter(erp=data.erp, user=data.niko, value=Vote.NEGATIVE_VALUE, comment="bouh").count() == 0

    # test email notification verify not send.
    assert len(mail.outbox) == 0


def test_erp_vote_counts(data, client, mocker):
    mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)

    # ERP is owner by user, this vote should not count
    client.force_login(data.niko)

    client.post(
        reverse("erp_vote", kwargs={"erp_slug": data.erp.slug}),
        {"action": "DOWN", "comment": "bouh niko"},
        follow=True,
    )

    assert Vote.objects.filter(erp=data.erp, value=Vote.POSITIVE_VALUE).count() == 0
    assert Vote.objects.filter(erp=data.erp, value=Vote.NEGATIVE_VALUE).count() == 0
    mock_mail.assert_not_called()

    # Another user, this should count
    client.force_login(data.sophie)

    client.post(
        reverse("erp_vote", kwargs={"erp_slug": data.erp.slug}),
        {"action": "DOWN", "comment": "bouh sophie"},
        follow=True,
    )

    assert mock_mail.call_count == 2
    call1, call2 = mock_mail.call_args_list

    assert call1.kwargs == {
        "to_list": data.sophie.email,
        "subject": None,
        "template": "vote_down",
        "context": {"erp_contrib_url": f"http://testserver/contrib/edit-infos/{data.erp.slug}/"},
    }

    assert call2.kwargs == {
        "to_list": "acceslibre@beta.gouv.fr",
        "subject": None,
        "template": "vote_down_admin",
        "context": {
            "username": data.sophie.username,
            "erp_nom": "Aux bons croissants",
            "erp_absolute_url": f"/app/34-jacou/a/boulangerie/erp/{data.erp.slug}/",
            "comment": "bouh sophie",
            "user_email": data.sophie.email,
        },
    }

    mock_mail.reset_mock()

    assert Vote.objects.filter(erp=data.erp, value=Vote.POSITIVE_VALUE).count() == 0
    vote_down = Vote.objects.get(erp=data.erp, value=Vote.NEGATIVE_VALUE)
    assert vote_down.comment == "bouh sophie"
    assert vote_down.user == data.sophie

    client.force_login(data.admin)

    client.post(
        reverse("erp_vote", kwargs={"erp_slug": data.erp.slug}),
        {"action": "UP"},
        follow=True,
    )
    mock_mail.assert_not_called()
    vote_up = Vote.objects.get(erp=data.erp, value=Vote.POSITIVE_VALUE)
    assert vote_up.user == data.admin
    assert Vote.objects.filter(erp=data.erp, value=Vote.NEGATIVE_VALUE).count() == 1


def test_erp_user_can_unvote_when_existing_vote(data, client, mocker):
    mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)
    client.force_login(data.sophie)
    Vote.objects.create(user=data.sophie, erp=data.erp, value=Vote.NEGATIVE_VALUE, comment="Data is incorrect")

    client.post(
        reverse("erp_vote", kwargs={"erp_slug": data.erp.slug}),
        {"action": "UNVOTE_DOWN"},
        follow=True,
    )

    mock_mail.assert_not_called()
    assert Vote.objects.filter(erp=data.erp, user=data.sophie).count() == 0


def test_vote_form_on_erp_details_page(data, client):
    client.force_login(data.sophie)

    response = client.get(data.erp.get_absolute_url())

    post_url = reverse("erp_vote", kwargs={"erp_slug": data.erp.slug})
    assert post_url in str(response.content)

    tracking_string_vote_down = f'data-track-event="vote,down,{data.erp.slug}"'
    assert tracking_string_vote_down in str(response.content)

    tracking_string_vote_up = f'data-track-event="vote,up,{data.erp.slug}"'
    assert tracking_string_vote_up in str(response.content)


def test_vote_form_changes_when_user_has_vote(data, client):
    client.force_login(data.sophie)
    Vote.objects.create(value=Vote.POSITIVE_VALUE, user=data.sophie, erp=data.erp)

    response = client.get(data.erp.get_absolute_url())

    post_url = reverse("erp_vote", kwargs={"erp_slug": data.erp.slug})
    assert post_url in str(response.content)

    tracking_string_vote_down = f'data-track-event="vote,down,{data.erp.slug}"'
    assert tracking_string_vote_down in str(response.content)

    tracking_string_unvote_up = f'data-track-event="vote,unvote_up,{data.erp.slug}"'
    assert tracking_string_unvote_up in str(response.content)
