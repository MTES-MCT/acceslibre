import uuid
from copy import copy

import pytest
import reversion
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import Client
from django.urls import reverse

from compte.models import UserStats
from erp.models import Accessibilite, Activite, ActivitySuggestion, Erp
from tests.factories import ErpFactory
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
        # Core
        "/sitemap.xml",
        "/robots.txt",
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


def test_auth(data, client):
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


def test_auth_using_email(data, client):
    response = client.post(
        reverse("login"),
        data={"username": "niko@niko.tld", "password": "Abc12345!"},
    )
    assert response.status_code == 302
    assert response.wsgi_request.user.username == "niko"


def test_registration(data, client):
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


def test_registration_with_first_and_last_name(data, client):
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
    assert User.objects.filter(username="julien", first_name="", last_name="", is_active=False).count() == 1


def test_registration_not_a_robot(data, client):
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
def test_registration_username_blacklisted(username, data, client):
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


def test_admin_with_regular_user(data, client):
    # test that regular frontend user don't have access to the admin
    client.force_login(data.samuel)

    response = client.get(reverse("admin:index"), follow=True)
    # ensure user is redirected to admin login page
    assert_redirect(response, "/admin/login/?next=/admin/")
    assert response.status_code == 200
    assert "admin/login.html" in [t.name for t in response.templates]


def test_admin_with_staff_user(data, client):
    # the staff flag is for partners (gestionnaire ou territoire)
    client.force_login(data.niko)

    response = client.get(reverse("admin:index"))
    assert response.status_code == 200

    response = client.get(reverse("admin:erp_erp_changelist"))
    assert response.status_code == 403


def test_admin_with_admin_user(data, client):
    client.force_login(data.admin)

    response = client.get(reverse("admin:index"))
    assert response.status_code == 200

    response = client.get(reverse("admin:erp_erp_changelist"))
    assert response.status_code == 200

    response = client.get(reverse("admin:erp_erp_add"))
    assert response.status_code == 200

    response = client.get(data.erp.get_admin_url())
    assert response.status_code == 200


def test_ajout_erp_without_auth(data, client):
    response = client.get(reverse("contrib_start"), follow=True)

    assert response.status_code == 200
    assert "contrib/0-start.html" in [t.name for t in response.templates]


def test_erp_edit_can_be_contributed(data, client):
    response = client.get(reverse("contrib_transport", kwargs={"erp_slug": data.erp.slug}), follow=True)

    assert response.status_code == 200


def test_ajout_erp(data, client):
    data.niko.stats.refresh_from_db()
    initial_nb_created = data.niko.stats.nb_erp_created
    initial_nb_edited = data.niko.stats.nb_erp_edited

    response = client.get(reverse("contrib_start"))
    assert response.status_code == 200

    response = client.get(reverse("contrib_admin_infos"))
    assert response.status_code == 200

    # Admin infos
    response = client.post(
        reverse("contrib_admin_infos"),
        data={
            "source": "sirene",
            "source_id": "xxx",
            "nom": "Test ERP",
            "activite": data.boulangerie.nom,
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
    assert erp.geom.x == 3
    assert erp.geom.y == 43
    assert erp.voie == "Grand rue", "Should have been normalized with geocode result"
    assert erp.geoloc_provider == "ban"
    assert erp.ban_id == "abcd_12345"
    assert not hasattr(erp, "accessibilite")
    assert erp.activite is not None
    assert_redirect(response, f"/contrib/a-propos/{erp.slug}/")
    assert response.status_code == 200

    # A propos
    response = client.post(
        reverse("contrib_a_propos", kwargs={"erp_slug": erp.slug}),
        data={"conformite": True, "user_type": Erp.USER_ROLE_ADMIN},
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert accessibilite.conformite is True
    assert accessibilite.completion_rate == 0
    assert_redirect(response, f"/contrib/transport/{erp.slug}/")

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
    assert accessibilite.completion_rate == 14
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
    assert accessibilite.completion_rate == 19
    assert_redirect(response, "/contrib/entree/test-erp/")
    assert response.status_code == 200

    # Entree
    response = client.post(
        reverse("contrib_entree", kwargs={"erp_slug": erp.slug}),
        data={
            "entree_porte_presence": True,
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
    assert accessibilite.entree_porte_presence is True
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
    assert accessibilite.completion_rate == 57
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
            "accueil_audiodescription_presence": True,
            "accueil_audiodescription": ["sans_équipement"],
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
    assert accessibilite.accueil_audiodescription_presence is True
    assert accessibilite.accueil_audiodescription == ["sans_équipement"]
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
    assert accessibilite.completion_rate == 90
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
    assert accessibilite.completion_rate == 100
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

    data.niko.stats.refresh_from_db()
    assert data.niko.stats.nb_erp_created == initial_nb_created + 1
    assert data.niko.stats.nb_erp_edited == initial_nb_edited


def test_ajout_erp_a11y_vide(data, client):
    client.force_login(data.niko)

    data.erp.published = False
    data.erp.save()
    # empty a11y data
    data.erp.accessibilite.sanitaires_presence = None
    data.erp.accessibilite.sanitaires_adaptes = None
    data.erp.accessibilite.entree_porte_presence = None
    data.erp.accessibilite.entree_reperage = None
    data.erp.accessibilite.commentaire = None
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

    assert_redirect(response, reverse("contrib_commentaire", kwargs={"erp_slug": data.erp.slug}))
    assert response.status_code == 200
    assert (
        str(response.context["messages"]._get()[0][0])
        == "Vous n'avez pas fourni assez d'infos d'accessibilité. Votre établissement ne peut pas être publié."
    )
    erp = Erp.objects.get(slug=data.erp.slug)
    assert erp.accessibilite.has_data() is False
    assert erp.published is False


def test_add_erp_duplicate(data, client):
    client.force_login(data.niko)
    data.niko.stats.refresh_from_db()
    initial_nb_created = data.niko.stats.nb_erp_created

    response = client.post(
        reverse("contrib_admin_infos"),
        data={
            "source": "sirene",
            "source_id": "xxx",
            "nom": "Test ERP",
            "activite": data.erp.activite.nom,
            "numero": data.erp.numero,
            "voie": data.erp.voie,
            "lieu_dit": "",
            "code_postal": data.erp.code_postal,
            "commune": data.erp.commune,
            "lat": 43,
            "lon": 3,
        },
        follow=True,
    )

    assert "existe déjà dans la base de données" in response.context["form"].errors["__all__"][0]
    assert not Erp.objects.filter(nom="Test ERP").exists(), "Should not have been created"
    data.niko.stats.refresh_from_db()
    assert data.niko.stats.nb_erp_created == initial_nb_created


def test_add_erp_missing_activity(data, client):
    client.force_login(data.niko)

    response = client.post(
        reverse("contrib_admin_infos"),
        data={
            "source": "sirene",
            "source_id": "xxx",
            "nom": "Test ERP",
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

    assert response.context["form"].errors == {"activite": ["Ce champ est obligatoire."]}
    assert not Erp.objects.filter(nom="Test ERP").exists(), "Should not have been created"


def test_add_erp_other_activity(data, client):
    assert ActivitySuggestion.objects.count() == 0

    client.force_login(data.niko)
    data.niko.stats.refresh_from_db()
    initial_nb_created = data.niko.stats.nb_erp_created

    client.post(
        reverse("contrib_admin_infos"),
        data={
            "source": "sirene",
            "source_id": "xxx",
            "nom": "Test ERP",
            "numero": "12",
            "voie": "GRAND RUE",
            "lieu_dit": "",
            "code_postal": "34830",
            "commune": "JACOU",
            "lat": 43,
            "lon": 3,
            "activite": Activite.objects.get(nom="Autre").nom,
            "nouvelle_activite": "My suggestion",
        },
        follow=True,
    )

    assert Erp.objects.get(nom="Test ERP", user=data.niko), "ERP should have been created and attributed to niko"

    assert ActivitySuggestion.objects.count() == 1
    activity_suggest = ActivitySuggestion.objects.last()
    assert activity_suggest.erp is not None
    assert activity_suggest.name == "My suggestion"
    assert activity_suggest.user == data.niko

    data.niko.stats.refresh_from_db()
    assert data.niko.stats.nb_erp_created == initial_nb_created + 1


def test_add_erp_with_profanities(data, client):
    assert UserStats.objects.get(user=data.sophie).nb_profanities == 0

    client.force_login(data.sophie)
    erp = data.erp

    client.post(
        reverse("contrib_commentaire", kwargs={"erp_slug": erp.slug}),
        data={"labels_autre": "barrez-vous, cons de mimes", "commentaire": "foo"},
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert not accessibilite.labels_autre, "Comment with profanities should not be stored"

    assert UserStats.objects.get(user=data.sophie).nb_profanities == 1
    data.sophie.refresh_from_db()
    assert data.sophie.is_active is True

    client.post(
        reverse("contrib_commentaire", kwargs={"erp_slug": erp.slug}),
        data={
            "commentaire": "bite",
        },
        follow=True,
    )
    accessibilite = Accessibilite.objects.get(erp__slug=erp.slug)
    assert (
        accessibilite.commentaire == "foo"
    ), "Comment with profanities should be ignored and reversed to the previous stored comment"
    assert UserStats.objects.get(user=data.sophie).nb_profanities == 2
    data.sophie.refresh_from_db()
    assert data.sophie.is_active is False


def test_delete_erp_unauthorized(data, client):
    client.force_login(data.sophie)

    response = client.get(reverse("contrib_delete", kwargs={"erp_slug": data.erp.slug}))
    assert response.status_code == 404


def test_delete_erp_owner(data, client):
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
        reversion.set_user(data.niko)
        erp.save()
        accessibilite = Accessibilite(erp=erp)
        accessibilite.save()

    with reversion.create_revision():
        erp.siret = "52128577500017"
        erp.published = False
        erp.geom = Point(1, 1)
        reversion.set_user(data.niko)

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
    assert str(get_entry("labels", a11y_diff)["old"]) == "Vide"
    assert str(get_entry("labels", a11y_diff)["new"]) == "Destination pour Tous, Tourisme & Handicap"


def test_contribution_flow_administrative_data(data, client):
    data.sophie.stats.refresh_from_db()
    initial_nb_created = data.sophie.stats.nb_erp_created
    initial_nb_edited = data.sophie.stats.nb_erp_edited

    client.force_login(data.sophie)
    response = client.get(reverse("contrib_edit_infos", kwargs={"erp_slug": data.erp.slug}))

    assert response.status_code == 200

    response = client.post(
        reverse("contrib_edit_infos", kwargs={"erp_slug": data.erp.slug}),
        data={
            "source": "sirene",
            "source_id": "xxx",
            "nom": "Test contribution",
            "activite": data.boulangerie.nom,
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

    data.sophie.stats.refresh_from_db()
    assert data.sophie.stats.nb_erp_created == initial_nb_created
    assert data.sophie.stats.nb_erp_edited == initial_nb_edited + 1


def test_contribution_flow_accessibilite_data(data, client):
    response = client.get(reverse("contrib_transport", kwargs={"erp_slug": data.erp.slug}))
    assert response.status_code == 200

    data.niko.stats.refresh_from_db()
    initial_nb_edited = data.niko.stats.nb_erp_edited

    client.post(
        reverse("contrib_transport", kwargs={"erp_slug": data.erp.slug}),
        data={
            "transport_station_presence": "False",
            "contribute": "Continuer",
        },
        follow=True,
    )
    updated_erp = Erp.objects.get(slug=data.erp.slug)
    assert updated_erp.accessibilite.transport_station_presence is None

    client.force_login(data.niko)
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

    data.niko.stats.refresh_from_db()
    assert data.niko.stats.nb_erp_edited == initial_nb_edited + 1


def test_erp_redirect(client, data):
    response = client.get(
        reverse("erp_uuid", kwargs={"uuid": str(data.erp.uuid)}),
        follow=True,
    )

    assert response.status_code == 200
    assert response.context["erp"] == data.erp

    response = client.get(
        reverse(
            "commune_activite_erp",
            kwargs={"commune": "foo", "activite_slug": "bar", "erp_slug": data.erp.slug},
        ),
        follow=True,
    )
    assert response.status_code == 200
    assert response.context["erp"] == data.erp
    assert response.redirect_chain == [("/app/34-jacou/a/boulangerie/erp/aux-bons-croissants/", 302)]


def test_edit_erp_invalid_data(data, client):
    client.force_login(data.niko)
    initial_erp = copy(data.erp)
    payload = {
        "lat": "http://i-want-to-hack-you.com/spam.exe",
    }
    response = client.post(
        reverse("contrib_edit_infos", kwargs={"erp_slug": data.erp.slug}),
        payload,
        follow=True,
    )

    data.erp.refresh_from_db()
    assert "lat" in response.context["form"].errors
    assert data.erp.geom.x == initial_erp.geom.x


@pytest.mark.django_db
def test_get_erp_by_uuid(client):
    response = client.get(reverse("erp_uuid", kwargs={"uuid": uuid.uuid4()}))
    assert response.status_code == 404

    erp = ErpFactory(published=True)

    response = client.get(reverse("erp_uuid", kwargs={"uuid": erp.uuid}))
    assert response.status_code == 302
    assert erp.slug in response.url

    erp.published = False
    erp.save()
    response = client.get(reverse("erp_uuid", kwargs={"uuid": erp.uuid}))
    assert response.status_code == 404, "should receive a 404 for a non published ERP"


@pytest.mark.django_db
def test_can_update_checked_up_to_date_at_from_erp(client):
    erp = ErpFactory(published=True)

    assert erp.checked_up_to_date_at is None

    response = client.post(reverse("confirm_up_to_date", kwargs={"erp_slug": erp.slug}))
    assert response.status_code == 302
    assert erp.slug in response.url

    erp.refresh_from_db()
    assert erp.checked_up_to_date_at is not None
