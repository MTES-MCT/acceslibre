import pytest
import reversion

from datetime import date

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core import mail
from django.test import Client
from django.urls import reverse

from erp import schema
from erp.models import Accessibilite, Activite, Commune, Erp, Vote
from erp.provider import geocoder

from tests.utils import assert_redirect


@pytest.fixture
def client():
    return Client()


def test_home(data, client):
    response = client.get(reverse("home"))
    assert response.status_code == 200


def test_communes(data, client):
    response = client.get(reverse("communes"))
    assert len(response.context["communes"]) == 1
    assert response.context["communes"][0].nom == "Jacou"
    assert len(response.context["latest"]) == 1


def test_search_clean_params(data, client):
    response = client.get(
        reverse("search") + "?where=None&what=None&lat=None&lon=None&code=None"
    )
    assert response.context["where"] == "France entière"
    assert response.context["what"] == ""
    assert response.context["lat"] == ""
    assert response.context["lon"] == ""
    assert response.context["code"] == ""


def test_search_pagination(data, client):
    data.erp.delete()
    for i in range(1, 22):
        erp = Erp.objects.create(
            nom=f"e{i}",
            commune_ext=data.jacou,
            geom=data.erp.geom,
            published=True,
        )
        Accessibilite.objects.create(erp=erp, sanitaires_presence=True)
    assert Erp.objects.published().count() == 21
    response = client.get(reverse("search") + "?where=jacou&code=34120&page=1")
    assert response.status_code == 200
    assert response.context["pager"].paginator.num_pages == 3
    assert len(response.context["pager"]) == 10
    response = client.get(reverse("search") + "?where=jacou&code=34120&page=2")
    assert response.status_code == 200
    assert len(response.context["pager"]) == 10
    response = client.get(reverse("search") + "?where=jacou&code=34120&page=3")
    assert response.status_code == 200
    assert len(response.context["pager"]) == 1


def test_search_commune(data, client, mocker):
    mocker.patch("erp.provider.geocoder.autocomplete", return_value=None)
    response = client.get(
        reverse("search") + "?where=Jacou&what=croissant&lat=43.661&lon=3.912"
    )
    assert response.context["where"] == "Jacou"
    assert response.context["what"] == "croissant"
    assert len(response.context["pager"]) == 1
    assert response.context["pager"][0].nom == "Aux bons croissants"
    assert hasattr(response.context["pager"][0], "distance") is True


def test_search_raw_commune(data, client, mocker):
    mocker.patch("erp.provider.geocoder.autocomplete", return_value=None)
    response = client.get(reverse("search") + "?where=jacou&what=croissant")
    assert response.context["where"] == "jacou"
    assert response.context["what"] == "croissant"
    assert len(response.context["pager"]) == 1
    assert response.context["pager"][0].nom == "Aux bons croissants"
    assert hasattr(response.context["pager"][0], "distance") is False


def test_search_qualified_commune(data, client, mocker):
    mocker.patch("erp.provider.geocoder.autocomplete", return_value=None)
    response = client.get(
        reverse("search_commune", kwargs={"commune_slug": "34-jacou"})
    )
    assert response.context["where"] == "Jacou (34)"
    assert len(response.context["pager"]) == 1
    assert response.context["pager"][0].nom == "Aux bons croissants"
    assert hasattr(response.context["pager"][0], "distance") is False


def test_search_empty_text_query(data, client, mocker):
    mocker.patch("erp.provider.geocoder.autocomplete", return_value=None)
    response = client.get(reverse("search") + "?where=&what=")
    assert response.context["where"] == "France entière"
    assert response.context["what"] == ""
    assert response.context["pager"] is not None


def test_search_around_me(data, client, mocker):
    mocker.patch("erp.provider.geocoder.autocomplete", return_value=None)
    response = client.get(
        reverse("search")
        + "?where=around_me&what=croissant&lat=43.6648062&lon=3.9048148"
    )
    assert response.context["where"] == "around_me"
    assert response.context["what"] == "croissant"
    assert len(response.context["pager"]) == 1
    assert response.context["pager"][0].nom == "Aux bons croissants"
    assert hasattr(response.context["pager"][0], "distance")


def test_invalid_search_params_404(data, client):
    response = client.get(reverse("search") + "?where=&what=&lat=INVALID&lon=INVALID")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "url",
    [
        # Home
        reverse("home"),
        # Communes
        reverse("communes"),
        # Search
        reverse("search"),
        reverse("search") + "?what=boulangerie",
        reverse("search") + "?where=jacou",
        reverse("search") + "?where=jacou&what=boulangerie",
        reverse("search") + "?where=jacou&what=boulangerie&lat=43.2&lon=2.39",
        reverse("search_commune", kwargs={"commune_slug": "34-jacou"}),
        # Editorial
        reverse("accessibilite"),
        reverse("cgu"),
        reverse("partenaires"),
        reverse("contact_form"),
        # Auth
        reverse("login"),
        reverse("django_registration_activation_complete"),
        reverse("password_reset"),
        reverse("password_reset_done"),
        reverse("django_registration_register"),
        reverse("django_registration_disallowed"),
        reverse("django_registration_complete"),
        reverse("password_reset_complete"),
        # App
        reverse(
            "commune_activite_erp",
            kwargs=dict(
                commune="34-jacou",
                activite_slug="boulangerie",
                erp_slug="aux-bons-croissants",
            ),
        ),
    ],
)
def test_urls_ok(data, url, client):
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "url",
    [
        reverse("admin:index"),
        reverse("admin:admin_logentry_changelist"),
        reverse("admin:auth_group_changelist"),
        reverse("admin:auth_user_changelist"),
        reverse("admin:contact_message_changelist"),
        reverse("admin:erp_activite_changelist"),
        reverse("admin:erp_commune_changelist"),
        reverse("admin:erp_erp_changelist"),
        reverse("admin:erp_vote_changelist"),
    ],
)
def test_admin_urls_ok(data, url, client):
    client.force_login(data.admin)
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "url",
    [
        reverse("mon_compte"),
        reverse("mes_erps"),
        reverse("mes_abonnements"),
        reverse("mes_contributions"),
        reverse("mes_contributions_recues"),
    ],
)
def test_admin_urls_ok(data, url, client):
    client.force_login(data.niko)
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "url",
    [
        reverse(
            "commune_activite_erp",
            kwargs=dict(commune="invalid", activite_slug="invalid", erp_slug="invalid"),
        ),
    ],
)
def test_urls_404(data, url, client):
    response = client.get(url)
    assert response.status_code == 404


def test_auth(data, client, capsys):
    response = client.post(
        reverse("login"),
        data={"username": "niko", "password": "Abc12345!"},
    )
    assert response.status_code == 302
    assert response.wsgi_request.user.username == "niko"

    response = client.get(reverse("mon_compte"))
    assert response.status_code == 200

    response = client.get(reverse("mes_erps"))
    assert response.status_code == 200
    assert response.context["pager"][0].nom == "Aux bons croissants"


def test_auth_using_email(data, client, capsys):
    response = client.post(
        reverse("login"),
        data={"username": "niko@niko.tld", "password": "Abc12345!"},
    )
    assert response.status_code == 302
    assert response.wsgi_request.user.username == "niko"


def test_registration(data, client, capsys):
    response = client.post(
        reverse("django_registration_register"),
        data={
            "username": "julien",
            "email": "julien@julien.tld",
            "password1": "Abc12345!",
            "password2": "Abc12345!",
            "robot": "on",
        },
    )
    assert response.status_code == 302
    # TODO: test activation link
    assert User.objects.filter(username="julien", is_active=False).count() == 1


def test_registration_with_first_and_last_name(data, client, capsys):
    response = client.post(
        reverse("django_registration_register"),
        data={
            "username": "julien",
            "email": "julien@julien.tld",
            "password1": "Abc12345!",
            "password2": "Abc12345!",
            "robot": "on",
        },
    )
    assert response.status_code == 302
    assert (
        User.objects.filter(
            username="julien", first_name="", last_name="", is_active=False
        ).count()
        == 1
    )


def test_registration_not_a_robot(data, client, capsys):
    response = client.post(
        reverse("django_registration_register"),
        data={
            "username": "julien",
            "email": "julien@julien.tld",
            "password1": "Abc12345!",
            "password2": "Abc12345!",
        },
    )
    assert response.status_code == 200
    assert "robot" in response.context["form"].errors
    assert User.objects.filter(username="julien").count() == 0


@pytest.mark.parametrize(
    "username",
    [
        "Admin",
        "commercial",
        "Commercial",
        "  commercial  ",
        "  Commercial  ",
    ],
)
def test_registration_username_blacklisted(username, data, client, capsys):
    response = client.post(
        reverse("django_registration_register"),
        data={
            "username": username,
            "email": "hacker@yoyo.tld",
            "password1": "Abc12345!",
            "password2": "Abc12345!",
            "robot": "on",
        },
    )
    assert response.status_code == 200
    assert User.objects.filter(username=username).count() == 0
    assert "username" in response.context["form"].errors


def test_admin_with_regular_user(data, client, capsys):
    # test that regular frontend user don't have access to the admin
    client.force_login(data.samuel)

    response = client.get(reverse("admin:index"), follow=True)
    # ensure user is redirected to admin login page
    assert_redirect(response, "/admin/login/?next=/admin/")
    assert response.status_code == 200
    assert "admin/login.html" in [t.name for t in response.templates]


def test_admin_with_staff_user(data, client, capsys):
    # the staff flag is for partners (gestionnaire ou territoire)
    client.force_login(data.niko)

    response = client.get(reverse("admin:index"))
    assert response.status_code == 200

    response = client.get(reverse("admin:erp_erp_changelist"))
    assert response.status_code == 403


def test_admin_with_admin_user(data, client, capsys):
    client.force_login(data.admin)

    response = client.get(reverse("admin:index"))
    assert response.status_code == 200

    response = client.get(reverse("admin:erp_erp_changelist"))
    assert response.status_code == 200

    response = client.get(reverse("admin:erp_erp_add"))
    assert response.status_code == 200

    response = client.get(data.erp.get_admin_url())
    assert response.status_code == 200


def test_ajout_erp_witout_auth(data, client):
    response = client.get(reverse("contrib_start"), follow=True)

    assert response.status_code == 200
    assert "contrib/0-start.html" in [t.name for t in response.templates]


def test_erp_edit_can_be_contributed(data, client):
    response = client.get(
        reverse("contrib_transport", kwargs={"erp_slug": data.erp.slug}), follow=True
    )

    assert response.status_code == 200


def test_ajout_erp(data, client, monkeypatch, capsys):
    response = client.get(reverse("contrib_start"))
    assert response.status_code == 200

    response = client.get(reverse("contrib_admin_infos"))
    assert response.status_code == 200

    # Admin infos
    def mock_geocode(*args, **kwargs):
        return {
            "geom": Point(0, 0),
            "numero": "12",
            "voie": "Grand rue",
            "lieu_dit": None,
            "code_postal": "34830",
            "commune": "Jacou",
            "code_insee": "34122",
        }

    monkeypatch.setattr(geocoder, "geocode", mock_geocode)

    response = client.post(
        reverse("contrib_admin_infos"),
        data={
            "source": "sirene",
            "source_id": "xxx",
            "nom": "Test ERP",
            "activite": data.boulangerie.pk,
            "numero": "12",
            "voie": "GRAND RUE",
            "lieu_dit": "",
            "code_postal": "34830",
            "commune": "JACOU",
            "lat": 43,
            "lon": 3,
        },
        follow=True,
    )
    erp = Erp.objects.get(nom="Test ERP")
    assert erp.user is None
    assert erp.published is False
    assert erp.geom.x == 0.0
    assert erp.geom.y == 0.0
    assert_redirect(response, f"/contrib/transport/{erp.slug}/")
    assert response.status_code == 200

    # Transport
    response = client.post(
        reverse("contrib_transport", kwargs={"erp_slug": erp.slug}),
        data={
            "transport_station_presence": True,
            "transport_information": "blah",
            "stationnement_presence": True,
            "stationnement_pmr": True,
            "stationnement_ext_presence": True,
            "stationnement_ext_pmr": True,
        },
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert accessibilite.transport_station_presence is True
    assert accessibilite.transport_information == "blah"
    assert accessibilite.stationnement_presence is True
    assert accessibilite.stationnement_pmr is True
    assert accessibilite.stationnement_ext_presence is True
    assert accessibilite.stationnement_ext_pmr is True
    assert_redirect(response, "/contrib/exterieur/test-erp/")

    assert response.status_code == 200

    # Extérieur
    response = client.post(
        reverse("contrib_exterieur", kwargs={"erp_slug": erp.slug}),
        data={
            "cheminement_ext_presence": True,
            "cheminement_ext_terrain_stable": True,
            "cheminement_ext_plain_pied": False,
            "cheminement_ext_ascenseur": True,
            "cheminement_ext_nombre_marches": 42,
            "cheminement_ext_sens_marches": "descendant",
            "cheminement_ext_reperage_marches": True,
            "cheminement_ext_main_courante": True,
            "cheminement_ext_rampe": "aucune",
            "cheminement_ext_pente_presence": True,
            "cheminement_ext_pente_degre_difficulte": "légère",
            "cheminement_ext_pente_longueur": "courte",
            "cheminement_ext_devers": "aucun",
            "cheminement_ext_bande_guidage": True,
            "cheminement_ext_retrecissement": True,
        },
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert accessibilite.cheminement_ext_presence is True
    assert accessibilite.cheminement_ext_terrain_stable is True
    assert accessibilite.cheminement_ext_plain_pied is False
    assert accessibilite.cheminement_ext_ascenseur is True
    assert accessibilite.cheminement_ext_nombre_marches == 42
    assert accessibilite.cheminement_ext_sens_marches == "descendant"
    assert accessibilite.cheminement_ext_reperage_marches is True
    assert accessibilite.cheminement_ext_main_courante is True
    assert accessibilite.cheminement_ext_rampe == "aucune"
    assert accessibilite.cheminement_ext_pente_presence is True
    assert accessibilite.cheminement_ext_pente_degre_difficulte == "légère"
    assert accessibilite.cheminement_ext_pente_longueur == "courte"
    assert accessibilite.cheminement_ext_devers == "aucun"
    assert accessibilite.cheminement_ext_bande_guidage is True
    assert accessibilite.cheminement_ext_retrecissement is True
    assert_redirect(response, "/contrib/entree/test-erp/")
    assert response.status_code == 200

    # Entree
    response = client.post(
        reverse("contrib_entree", kwargs={"erp_slug": erp.slug}),
        data={
            "entree_reperage": True,
            "entree_vitree": True,
            "entree_vitree_vitrophanie": True,
            "entree_plain_pied": False,
            "entree_ascenseur": True,
            "entree_marches": 42,
            "entree_marches_sens": "descendant",
            "entree_marches_reperage": True,
            "entree_marches_main_courante": True,
            "entree_marches_rampe": "aucune",
            "entree_balise_sonore": True,
            "entree_dispositif_appel": True,
            "entree_dispositif_appel_type": ["bouton", "visiophone"],
            "entree_aide_humaine": True,
            "entree_largeur_mini": 80,
            "entree_pmr": True,
            "entree_pmr_informations": "blah",
        },
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert accessibilite.entree_reperage is True
    assert accessibilite.entree_vitree is True
    assert accessibilite.entree_vitree_vitrophanie is True
    assert accessibilite.entree_plain_pied is False
    assert accessibilite.entree_ascenseur is True
    assert accessibilite.entree_marches == 42
    assert accessibilite.entree_marches_sens == "descendant"
    assert accessibilite.entree_marches_reperage is True
    assert accessibilite.entree_marches_main_courante is True
    assert accessibilite.entree_marches_rampe == "aucune"
    assert accessibilite.entree_balise_sonore is True
    assert accessibilite.entree_dispositif_appel is True
    assert accessibilite.entree_dispositif_appel_type == ["bouton", "visiophone"]
    assert accessibilite.entree_aide_humaine is True
    assert accessibilite.entree_largeur_mini == 80
    assert accessibilite.entree_pmr is True
    assert accessibilite.entree_pmr_informations == "blah"
    assert_redirect(response, "/contrib/accueil/test-erp/")
    assert response.status_code == 200

    # Accueil
    response = client.post(
        reverse("contrib_accueil", kwargs={"erp_slug": erp.slug}),
        data={
            "accueil_visibilite": True,
            "accueil_personnels": "aucun",
            "accueil_equipements_malentendants_presence": True,
            "accueil_equipements_malentendants": ["bim", "lsf"],
            "accueil_cheminement_plain_pied": False,
            "accueil_cheminement_ascenseur": True,
            "accueil_cheminement_nombre_marches": 42,
            "accueil_cheminement_sens_marches": "descendant",
            "accueil_cheminement_reperage_marches": True,
            "accueil_cheminement_main_courante": True,
            "accueil_cheminement_rampe": "aucune",
            "accueil_retrecissement": True,
            "sanitaires_presence": True,
            "sanitaires_adaptes": True,
        },
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert accessibilite.accueil_visibilite is True
    assert accessibilite.accueil_personnels == "aucun"
    assert accessibilite.accueil_equipements_malentendants_presence is True
    assert accessibilite.accueil_equipements_malentendants == ["bim", "lsf"]
    assert accessibilite.accueil_cheminement_plain_pied is False
    assert accessibilite.accueil_cheminement_ascenseur is True
    assert accessibilite.accueil_cheminement_nombre_marches == 42
    assert accessibilite.accueil_cheminement_sens_marches == "descendant"
    assert accessibilite.accueil_cheminement_reperage_marches is True
    assert accessibilite.accueil_cheminement_main_courante is True
    assert accessibilite.accueil_cheminement_rampe == "aucune"
    assert accessibilite.accueil_retrecissement is True
    assert accessibilite.sanitaires_presence is True
    assert accessibilite.sanitaires_adaptes is True
    assert_redirect(response, "/contrib/commentaire/test-erp/")
    assert response.status_code == 200

    # Commentaire
    response = client.post(
        reverse("contrib_commentaire", kwargs={"erp_slug": erp.slug}),
        data={
            "labels": ["th"],
            "labels_familles_handicap": ["visuel", "auditif"],
            "labels_autre": "X",
            "commentaire": "test commentaire",
        },
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert accessibilite.labels == ["th"]
    assert accessibilite.labels_familles_handicap == ["visuel", "auditif"]
    assert accessibilite.labels_autre == "X"
    assert accessibilite.commentaire == "test commentaire"
    assert_redirect(response, "/contrib/publication/test-erp/")
    assert response.status_code == 200

    # Publication
    # Public user
    client.force_login(data.niko)
    response = client.post(
        reverse("contrib_publication", kwargs={"erp_slug": erp.slug}),
        data={
            "published": "on",
        },
        follow=True,
    )
    erp = Erp.objects.get(slug=erp.slug)
    assert erp.published is True
    assert erp.user == data.niko
    assert_redirect(response, erp.get_absolute_url())
    assert response.status_code == 200


def test_ajout_erp_a11y_vide(data, client, capsys):
    client.force_login(data.niko)

    # empty a11y data
    data.erp.accessibilite.sanitaires_presence = None
    data.erp.accessibilite.sanitaires_adaptes = None
    data.erp.accessibilite.save()
    data.erp.save()

    assert data.erp.accessibilite.has_data() is False

    # published field on
    response = client.post(
        reverse("contrib_publication", kwargs={"erp_slug": data.erp.slug}),
        data={
            "published": "on",
        },
        follow=True,
    )

    assert_redirect(response, data.erp.get_absolute_url())
    assert response.status_code == 200
    erp = Erp.objects.get(slug=data.erp.slug)
    assert erp.accessibilite.has_data() is False
    assert erp.published is True

    # published field off
    response = client.post(
        reverse("contrib_publication", kwargs={"erp_slug": data.erp.slug}),
        follow=True,
    )

    assert_redirect(response, reverse("mes_erps"))
    erp = Erp.objects.get(slug=data.erp.slug)
    assert erp.published is False


def test_delete_erp_unauthorized(data, client, monkeypatch, capsys):
    client.force_login(data.sophie)

    response = client.get(reverse("contrib_delete", kwargs={"erp_slug": data.erp.slug}))
    assert response.status_code == 404


def test_delete_erp_owner(data, client, monkeypatch, capsys):
    client.force_login(data.niko)

    response = client.get(reverse("contrib_delete", kwargs={"erp_slug": data.erp.slug}))
    assert response.status_code == 200

    assert Erp.objects.filter(slug=data.erp.slug).count() == 1

    # non-confirmed submission
    response = client.post(
        reverse("contrib_delete", kwargs={"erp_slug": data.erp.slug}),
        data={"confirm": False},
    )

    assert response.status_code == 200
    assert "confirm" in response.context["form"].errors

    # confirmed submission
    response = client.post(
        reverse("contrib_delete", kwargs={"erp_slug": data.erp.slug}),
        data={"confirm": True},
        follow=True,
    )
    assert_redirect(response, "/compte/erps/")
    assert response.status_code == 200
    assert Erp.objects.filter(slug=data.erp.slug).count() == 0


def test_erp_vote_anonymous(data, client):
    response = client.post(
        reverse("erp_vote", kwargs={"erp_slug": data.erp.slug}),
        {"action": "DOWN", "comment": "bouh"},
        follow=True,
    )

    # ensure user is redirected to login page
    assert_redirect(response, "/compte/login/?next=/app/aux-bons-croissants/vote/")
    assert response.status_code == 200
    assert "registration/login.html" in [t.name for t in response.templates]


def test_erp_vote_logged_in(data, client):
    client.force_login(data.niko)

    response = client.post(
        reverse("erp_vote", kwargs={"erp_slug": data.erp.slug}),
        {"action": "DOWN", "comment": "bouh"},
        follow=True,
    )

    assert response.status_code == 400

    # Ensure votes are not counted
    assert (
        Vote.objects.filter(
            erp=data.erp, user=data.niko, value=-1, comment="bouh"
        ).count()
        == 0
    )

    # test email notification verify not send.
    assert len(mail.outbox) == 0


def test_erp_vote_counts(data, client):
    client.force_login(data.niko)

    client.post(
        reverse("erp_vote", kwargs={"erp_slug": data.erp.slug}),
        {"action": "DOWN", "comment": "bouh niko"},
        follow=True,
    )

    assert Vote.objects.filter(erp=data.erp, value=1).count() == 0
    assert Vote.objects.filter(erp=data.erp, value=-1).count() == 0

    client.force_login(data.sophie)

    client.post(
        reverse("erp_vote", kwargs={"erp_slug": data.erp.slug}),
        {"action": "DOWN", "comment": "bouh sophie"},
        follow=True,
    )

    assert Vote.objects.filter(erp=data.erp, value=1).count() == 0
    assert Vote.objects.filter(erp=data.erp, value=-1).count() == 1

    client.force_login(data.admin)

    client.post(
        reverse("erp_vote", kwargs={"erp_slug": data.erp.slug}),
        {"action": "UP"},
        follow=True,
    )

    assert Vote.objects.filter(erp=data.erp, value=1).count() == 1
    assert Vote.objects.filter(erp=data.erp, value=-1).count() == 1


def test_accessibilite_history(data, client):
    accessibilite = Accessibilite.objects.get(erp__slug=data.erp.slug)

    assert 0 == len(accessibilite.get_history())

    client.force_login(data.niko)
    client.post(
        reverse("contrib_transport", kwargs={"erp_slug": data.erp.slug}),
        data={"transport_station_presence": True},
    )
    client.post(
        reverse("contrib_transport", kwargs={"erp_slug": data.erp.slug}),
        data={"transport_station_presence": False},
    )
    accessibilite.refresh_from_db()
    history = accessibilite.get_history()

    assert 1 == len(history)
    assert history[0]["user"] == data.niko
    assert history[0]["diff"] == [
        {
            "field": "transport_station_presence",
            "label": "Proximité d'un arrêt de transport en commun",
            "new": "Non",
            "old": "Oui",
        },
    ]


def test_history_metadata_not_versioned(data, client):
    with reversion.create_revision():
        data.erp.metadata = {"a": 1}
        data.erp.save()

    with reversion.create_revision():
        data.erp.metadata = {"a": 2}
        data.erp.save()

    assert 0 == len(data.erp.get_history())


def test_history_human_readable_diff(data, client):
    with reversion.create_revision():
        erp = Erp(
            nom="test erp",
            siret="52128577500016",
            published=True,
            geom=Point(0, 0),
        )
        erp.save()
        accessibilite = Accessibilite(erp=erp)
        accessibilite.save()

    with reversion.create_revision():
        erp.siret = "52128577500017"
        erp.published = False
        erp.geom = Point(1, 1)
        erp.save()

        erp.accessibilite.cheminement_ext_nombre_marches = 42
        erp.accessibilite.labels = ["dpt", "th"]
        erp.accessibilite.save()

    history = erp.get_history()

    assert len(history) == 2  # one entry per call to model .save()

    erp_diff = history[0]["diff"]

    assert len(erp_diff) == 3

    def get_entry(field, diff_entries):
        return list(filter(lambda x: x["field"] == field, diff_entries))[0]

    assert get_entry("published", erp_diff)["old"] == "Oui"
    assert get_entry("published", erp_diff)["new"] == "Non"

    assert get_entry("geom", erp_diff)["old"] == "0.0000, 0.0000"
    assert get_entry("geom", erp_diff)["new"] == "1.0000, 1.0000"

    assert get_entry("siret", erp_diff)["old"] == "52128577500016"
    assert get_entry("siret", erp_diff)["new"] == "52128577500017"

    a11y_diff = history[1]["diff"]

    assert len(a11y_diff) == 2

    assert get_entry("cheminement_ext_nombre_marches", a11y_diff)["old"] == "Vide"
    assert get_entry("cheminement_ext_nombre_marches", a11y_diff)["new"] == "42"
    assert get_entry("labels", a11y_diff)["old"] == "Vide"
    assert (
        get_entry("labels", a11y_diff)["new"]
        == "Destination pour Tous, Tourisme & Handicap"
    )


def test_contribution_flow_administrative_data(data, mocker, client):
    mocker.patch(
        "erp.provider.geocoder.geocode",
        return_value={
            "geom": Point(0, 0),
            "numero": "4",
            "voie": "Grand Rue",
            "lieu_dit": None,
            "code_postal": "34830",
            "commune": "Jacou",
            "code_insee": "34120",
        },
    )
    client.force_login(data.sophie)
    response = client.get(
        reverse("contrib_edit_infos", kwargs={"erp_slug": data.erp.slug})
    )

    assert response.status_code == 200

    response = client.post(
        reverse("contrib_edit_infos", kwargs={"erp_slug": data.erp.slug}),
        data={
            "source": "sirene",
            "source_id": "xxx",
            "nom": "Test contribution",
            "activite": data.boulangerie.pk,
            "numero": "12",
            "voie": "GRAND RUE",
            "lieu_dit": "",
            "code_postal": "34830",
            "commune": "JACOU",
            "site_internet": "http://google.com/",
            "action": "contribute",
            "lat": data.erp.geom.x,
            "lon": data.erp.geom.y,
        },
        follow=True,
    )

    updated_erp = Erp.objects.get(slug=data.erp.slug)
    assert response.context["form"].errors == {}
    assert updated_erp.nom == "Test contribution"
    assert updated_erp.user == data.erp.user  # original owner is preserved
    assert_redirect(response, "/contrib/transport/aux-bons-croissants/")
    assert response.status_code == 200


def test_contribution_flow_accessibilite_data(data, client):
    response = client.get(
        reverse("contrib_transport", kwargs={"erp_slug": data.erp.slug})
    )

    assert response.status_code == 200

    response = client.post(
        reverse("contrib_transport", kwargs={"erp_slug": data.erp.slug}),
        data={
            "transport_station_presence": "False",
            "contribute": "Continuer",
        },
        follow=True,
    )

    updated_erp = Erp.objects.get(slug=data.erp.slug)
    assert updated_erp.user == data.erp.user  # original owner is preserved
    assert updated_erp.accessibilite.transport_station_presence is False
    assert_redirect(
        response,
        reverse("contrib_exterieur", kwargs={"erp_slug": updated_erp.slug}),
    )
    assert response.status_code == 200


def test_uuid_redirect(client, data):
    response = client.get(
        reverse("erp_uuid", kwargs={"uuid": str(data.erp.uuid)}),
        follow=True,
    )

    assert response.status_code == 200
    assert response.context["erp"] == data.erp
