import pytest

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import Client
from django.urls import reverse

from .. import geocoder
from ..models import Accessibilite, Activite, Commune, Erp

from .fixtures import data


@pytest.fixture
def client():
    return Client()


def test_home_communes(data, client):
    response = client.get(reverse("home"))
    assert response.context["search"] is None
    assert len(response.context["communes"]) == 1
    assert response.context["communes"][0].nom == "Jacou"
    assert len(response.context["latest"]) == 1
    assert response.context["search_results"] == None


def test_home_search(data, client):
    response = client.get(reverse("home") + "?q=croissant%20jacou")
    assert response.context["search"] == "croissant jacou"
    assert len(response.context["search_results"]["erps"]) == 1
    assert response.context["search_results"]["erps"][0].nom == "Aux bons croissants"


@pytest.mark.parametrize(
    "url",
    [
        # Home and search engine
        reverse("home"),
        reverse("home") + "?q=plop",
        # Editorial
        reverse("accessibilite"),
        reverse("autocomplete"),
        reverse("contact_form"),
        reverse("donnees_personnelles"),
        reverse("mentions_legales"),
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
        reverse("commune", kwargs=dict(commune="34-jacou")),
        reverse(
            "commune_activite",
            kwargs=dict(commune="34-jacou", activite_slug="boulangerie"),
        ),
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
        reverse("commune", kwargs=dict(commune="invalid")),
        reverse(
            "commune_activite", kwargs=dict(commune="invalid", activite_slug="invalid")
        ),
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
        reverse("login"), data={"username": "niko", "password": "Abc12345!"},
    )
    assert response.status_code == 302
    assert response.wsgi_request.user.username == "niko"

    response = client.get(reverse("mon_compte"))
    assert response.status_code == 200

    response = client.get(reverse("mes_erps"))
    assert response.status_code == 200
    assert response.context["pager"][0].nom == "Aux bons croissants"


def test_registration(data, client, capsys):
    response = client.post(
        reverse("django_registration_register"),
        data={
            "username": "julia",
            "email": "julia@julia.tld",
            "password1": "Abc12345!",
            "password2": "Abc12345!",
        },
    )
    assert response.status_code == 302
    # TODO: test activation link
    assert User.objects.filter(username="julia", is_active=False).count() == 1


def test_registration_with_first_and_last_name(data, client, capsys):
    response = client.post(
        reverse("django_registration_register"),
        data={
            "username": "julia",
            "first_name": "Julia",
            "last_name": "Zucker",
            "email": "julia@julia.tld",
            "password1": "Abc12345!",
            "password2": "Abc12345!",
        },
    )
    assert response.status_code == 302
    assert (
        User.objects.filter(
            username="julia", first_name="Julia", last_name="Zucker", is_active=False
        ).count()
        == 1
    )


def test_admin_with_regular_user(data, client, capsys):
    # test that regular frontend user don't have access to the admin
    client.login(username="julia", password="Abc12345!")

    response = client.get(reverse("admin:index"), follow=True)
    # ensure user is redirected to admin login page
    assert ("/admin/login/?next=/admin/", 302) in response.redirect_chain
    assert response.status_code == 200
    assert "admin/login.html" in [t.name for t in response.templates]


def test_admin_with_staff_user(data, client, capsys):
    # the staff flag is for partners (gestionnaire ou territoire)
    client.login(username="niko", password="Abc12345!")

    response = client.get(reverse("admin:index"))
    assert response.status_code == 200

    response = client.get(reverse("admin:erp_erp_changelist"))
    assert response.status_code == 403


def test_admin_with_admin_user(data, client, capsys):
    client.login(username="admin", password="Abc12345!")

    response = client.get(reverse("admin:index"))
    assert response.status_code == 200

    response = client.get(reverse("admin:erp_erp_changelist"))
    assert response.status_code == 200

    response = client.get(reverse("admin:erp_erp_add"))
    assert response.status_code == 200

    response = client.get(
        reverse("admin:erp_erp_change", kwargs=dict(object_id=data.erp.pk))
    )
    assert response.status_code == 200


def test_contact(data, client):
    from django.core import mail

    response = client.post(
        reverse("contact_form"),
        {"name": "Joe Test", "email": "joe@test.com", "body": "C'est un test"},
    )

    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert "Nouveau message" in mail.outbox[0].subject
    assert "Joe Test" in mail.outbox[0].body
    assert "joe@test.com" in mail.outbox[0].body
    assert "C'est un test" in mail.outbox[0].body


def test_ajout_erp_requires_auth(data, client):
    response = client.get(reverse("contrib_start"), follow=True)

    assert ("/accounts/login/?next=/contrib/start/", 302) in response.redirect_chain
    assert response.status_code == 200
    assert "registration/login.html" in [t.name for t in response.templates]


def test_erp_edit_restricted_to_owner(data, client):
    # owners can edit their erp
    client.login(username="niko", password="Abc12345!")
    response = client.get(
        reverse("contrib_transport", kwargs={"erp_slug": data.erp.slug})
    )
    assert response.status_code == 200

    # non-owner can't
    client.login(username="sophie", password="Abc12345!")
    response = client.get(
        reverse("contrib_transport", kwargs={"erp_slug": data.erp.slug})
    )
    assert response.status_code == 404


def test_ajout_erp_authenticated(data, client, monkeypatch, capsys):
    client.login(username="niko", password="Abc12345!")

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
            "nom": "Test ERP",
            "recevant_du_public": True,
            "activite": data.boulangerie.pk,
            "siret": "",
            "numero": "12",
            "voie": "GRAND RUE",
            "lieu_dit": "",
            "code_postal": "34830",
            "commune": "JACOU",
        },
        follow=True,
    )
    erp = Erp.objects.get(nom="Test ERP")
    assert erp.user == data.niko
    assert erp.published == False
    assert (f"/contrib/localisation/{erp.slug}/", 302) in response.redirect_chain
    assert response.status_code == 200

    # Localisation
    response = client.post(
        reverse("contrib_localisation", kwargs={"erp_slug": erp.slug}),
        data={"lat": "43", "lon": "3"},
        follow=True,
    )
    erp = Erp.objects.get(nom="Test ERP")
    assert erp.geom.x == 3
    assert erp.geom.y == 43
    assert ("/contrib/transport/test-erp/", 302) in response.redirect_chain
    assert response.status_code == 200

    # Transport
    response = client.post(
        reverse("contrib_transport", kwargs={"erp_slug": erp.slug}),
        data={"transport_station_presence": True, "transport_information": "blah"},
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert accessibilite.transport_station_presence == True
    assert accessibilite.transport_information == "blah"
    assert ("/contrib/stationnement/test-erp/", 302) in response.redirect_chain
    assert response.status_code == 200

    # Stationnement
    response = client.post(
        reverse("contrib_stationnement", kwargs={"erp_slug": erp.slug}),
        data={
            "stationnement_presence": True,
            "stationnement_pmr": True,
            "stationnement_ext_presence": True,
            "stationnement_ext_pmr": True,
        },
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert accessibilite.stationnement_presence == True
    assert accessibilite.stationnement_pmr == True
    assert accessibilite.stationnement_ext_presence == True
    assert accessibilite.stationnement_ext_pmr == True
    assert ("/contrib/exterieur/test-erp/", 302) in response.redirect_chain
    assert response.status_code == 200

    # Extérieur
    response = client.post(
        reverse("contrib_exterieur", kwargs={"erp_slug": erp.slug}),
        data={
            "cheminement_ext_presence": True,
            "cheminement_ext_terrain_accidente": True,
            "cheminement_ext_plain_pied": False,
            "cheminement_ext_ascenseur": True,
            "cheminement_ext_nombre_marches": 42,
            "cheminement_ext_reperage_marches": True,
            "cheminement_ext_main_courante": True,
            "cheminement_ext_rampe": "aucune",
            "cheminement_ext_pente": "aucune",
            "cheminement_ext_devers": "aucun",
            "cheminement_ext_bande_guidage": True,
            "cheminement_ext_retrecissement": True,
        },
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert accessibilite.cheminement_ext_presence == True
    assert accessibilite.cheminement_ext_terrain_accidente == True
    assert accessibilite.cheminement_ext_plain_pied == False
    assert accessibilite.cheminement_ext_ascenseur == True
    assert accessibilite.cheminement_ext_nombre_marches == 42
    assert accessibilite.cheminement_ext_reperage_marches == True
    assert accessibilite.cheminement_ext_main_courante == True
    assert accessibilite.cheminement_ext_rampe == "aucune"
    assert accessibilite.cheminement_ext_pente == "aucune"
    assert accessibilite.cheminement_ext_devers == "aucun"
    assert accessibilite.cheminement_ext_bande_guidage == True
    assert accessibilite.cheminement_ext_retrecissement == True
    assert ("/contrib/entree/test-erp/", 302) in response.redirect_chain
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
            "entree_marches_reperage": True,
            "entree_marches_main_courante": True,
            "entree_marches_rampe": "aucune",
            "entree_balise_sonore": True,
            "entree_dispositif_appel": True,
            "entree_aide_humaine": True,
            "entree_largeur_mini": 80,
            "entree_pmr": True,
            "entree_pmr_informations": "blah",
        },
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert accessibilite.entree_reperage == True
    assert accessibilite.entree_vitree == True
    assert accessibilite.entree_vitree_vitrophanie == True
    assert accessibilite.entree_plain_pied == False
    assert accessibilite.entree_ascenseur == True
    assert accessibilite.entree_marches == 42
    assert accessibilite.entree_marches_reperage == True
    assert accessibilite.entree_marches_main_courante == True
    assert accessibilite.entree_marches_rampe == "aucune"
    assert accessibilite.entree_balise_sonore == True
    assert accessibilite.entree_dispositif_appel == True
    assert accessibilite.entree_aide_humaine == True
    assert accessibilite.entree_largeur_mini == 80
    assert accessibilite.entree_pmr == True
    assert accessibilite.entree_pmr_informations == "blah"
    assert ("/contrib/accueil/test-erp/", 302) in response.redirect_chain
    assert response.status_code == 200

    # Accueil
    response = client.post(
        reverse("contrib_accueil", kwargs={"erp_slug": erp.slug}),
        data={
            "accueil_visibilite": True,
            "accueil_personnels": "aucun",
            "accueil_equipements_malentendants": ["bim", "lsf"],
            "accueil_cheminement_plain_pied": False,
            "accueil_cheminement_ascenseur": True,
            "accueil_cheminement_nombre_marches": 42,
            "accueil_cheminement_reperage_marches": True,
            "accueil_cheminement_main_courante": True,
            "accueil_cheminement_rampe": "aucune",
            "accueil_retrecissement": True,
            "accueil_prestations": "blah",
        },
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert accessibilite.accueil_visibilite == True
    assert accessibilite.accueil_personnels == "aucun"
    assert accessibilite.accueil_equipements_malentendants == ["bim", "lsf"]
    assert accessibilite.accueil_cheminement_plain_pied == False
    assert accessibilite.accueil_cheminement_ascenseur == True
    assert accessibilite.accueil_cheminement_nombre_marches == 42
    assert accessibilite.accueil_cheminement_reperage_marches == True
    assert accessibilite.accueil_cheminement_main_courante == True
    assert accessibilite.accueil_cheminement_rampe == "aucune"
    assert accessibilite.accueil_retrecissement == True
    assert accessibilite.accueil_prestations == "blah"
    assert ("/contrib/sanitaires/test-erp/", 302) in response.redirect_chain
    assert response.status_code == 200

    # Sanitaires
    response = client.post(
        reverse("contrib_sanitaires", kwargs={"erp_slug": erp.slug}),
        data={"sanitaires_presence": True, "sanitaires_adaptes": 42,},
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert accessibilite.sanitaires_presence == True
    assert accessibilite.sanitaires_adaptes == 42
    assert ("/contrib/autre/test-erp/", 302) in response.redirect_chain
    assert response.status_code == 200

    # Autre
    response = client.post(
        reverse("contrib_autre", kwargs={"erp_slug": erp.slug}),
        data={
            "sanitaires_adaptes": 42,
            "labels": [],
            "labels_familles_handicap": ["visuel", "auditif"],
            "labels_autre": "X",
            "commentaire": "Y",
        },
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert accessibilite.sanitaires_adaptes == 42
    assert accessibilite.labels.count() == 0
    assert accessibilite.labels_familles_handicap == ["visuel", "auditif"]
    assert accessibilite.labels_autre == "X"
    assert accessibilite.commentaire == "Y"
    assert ("/contrib/publication/test-erp/", 302) in response.redirect_chain
    assert response.status_code == 200

    # Publication
    # Public user
    response = client.post(
        reverse("contrib_publication", kwargs={"erp_slug": erp.slug}),
        data={"user_type": Erp.USER_ROLE_PUBLIC, "certif": True,},
        follow=True,
    )
    erp = Erp.objects.get(slug=erp.slug, user_type=Erp.USER_ROLE_PUBLIC)
    assert erp.published == True
    assert ("/mon_compte/erps/", 302) in response.redirect_chain
    assert response.status_code == 200
    # Administrative user
    response = client.post(
        reverse("contrib_publication", kwargs={"erp_slug": erp.slug}),
        data={"user_type": Erp.USER_ROLE_ADMIN, "certif": True,},
        follow=True,
    )
    erp = Erp.objects.get(slug=erp.slug, user_type=Erp.USER_ROLE_ADMIN)
    assert erp.published == True
    assert ("/mon_compte/erps/", 302) in response.redirect_chain
    assert response.status_code == 200
