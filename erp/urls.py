from django.contrib.auth import views as auth_views
from django.urls import include, path

from erp import schema, views

handler403 = views.handler403
handler404 = views.handler404
handler500 = views.handler500


def editorial_page(template_name, context=None):
    return views.EditorialView.as_view(template_name=template_name, extra_context=context)


urlpatterns = [
    ############################################################################
    # Editorial
    ############################################################################
    path(
        "",
        views.home,
        name="home",
    ),
    path(
        "mentions-legales",
        editorial_page("editorial/mention-legales.html"),
        name="mentions-legales",
    ),
    path(
        "politique-confidentialite",
        editorial_page("editorial/politique-confidentialite.html"),
        name="politique-confidentialite",
    ),
    path(
        "accessibilite",
        editorial_page("editorial/accessibilite.html"),
        name="accessibilite",
    ),
    path(
        "partenaires",
        editorial_page("editorial/partenaires.html", context={"partenaires": schema.PARTENAIRES}),
        name="partenaires",
    ),
    path(
        "qui-sommes-nous",
        views.about_us,
        name="about-us",
    ),
    # Challenge DDT mars 2022
    path("challenges/", views.challenges, name="challenges"),
    path("challenge/ddt/2022/03/", views.challenge_ddt, name="challenge-ddt"),
    path(
        "challenge/<str:challenge_slug>/",
        views.challenge_detail,
        name="challenge-detail",
    ),
    path(
        "challenge/<str:challenge_slug>/inscription/",
        views.challenge_inscription,
        name="challenge-inscription",
    ),
    path(
        "challenge/<str:challenge_slug>/desinscription/",
        views.challenge_unsubscription,
        name="challenge-unsubscription",
    ),
    # Map icons
    path("mapicons", views.mapicons, name="mapicons"),
    path(
        "communes/",
        views.communes,  # cached in template side
        name="communes",
    ),
    path(
        "export/",
        views.export,
        name="export",
    ),
    path(
        "recherche/",
        views.search,
        name="search",
    ),
    path(
        "recherche/<str:commune_slug>/",
        views.search_in_municipality,
        name="search_commune",
    ),
    path(
        "app/<str:commune>/erp/<str:erp_slug>/",
        views.erp_details,  # avoid caching details page
        name="commune_erp",
    ),
    path(
        "app/<str:commune>/a/<str:activite_slug>/erp/<str:erp_slug>/",
        views.erp_details,  # avoid caching details page
        name="commune_activite_erp",
    ),
    path(
        "app/<str:erp_slug>/confirm_up_to_date",
        views.confirm_up_to_date,
        name="confirm_up_to_date",
    ),
    path("uuid/<str:uuid>/", views.from_uuid, name="erp_uuid"),
    path("uuid/<str:uuid>/widget/", views.widget_from_uuid, name="widget_erp_uuid"),
    ############################################################################
    # Ajout ERP
    ############################################################################
    path(
        "contrib/documentation/",
        views.contrib_documentation,
        name="contrib_documentation",
    ),
    path("contrib/delete/<str:erp_slug>/", views.contrib_delete, name="contrib_delete"),
    path("contrib/start/", views.contrib_start, name="contrib_start"),
    path(
        "contrib/start/recherche/",
        views.contrib_global_search,
        name="contrib_global_search",
    ),
    path("contrib/admin-infos/", views.contrib_admin_infos, name="contrib_admin_infos"),
    path("contrib/v2/", include("erp.contribution.urls")),
    # NOTE: The next 8 URLs should not be renamed (at least without any back compatibility), used by Service Public.
    path(
        "contrib/edit-infos/<str:erp_slug>/",
        views.contrib_edit_infos,
        name="contrib_edit_infos",
    ),
    path(
        "contrib/a-propos/<str:erp_slug>/",
        views.contrib_a_propos,
        name="contrib_a_propos",
    ),
    path(
        "contrib/transport/<str:erp_slug>/",
        views.contrib_transport,
        name="contrib_transport",
    ),
    path(
        "contrib/exterieur/<str:erp_slug>/",
        views.contrib_exterieur,
        name="contrib_exterieur",
    ),
    path(
        "contrib/entree/<str:erp_slug>/",
        views.contrib_entree,
        name="contrib_entree",
    ),
    path(
        "contrib/accueil/<str:erp_slug>/",
        views.contrib_accueil,
        name="contrib_accueil",
    ),
    path(
        "contrib/commentaire/<str:erp_slug>/",
        views.contrib_commentaire,
        name="contrib_commentaire",
    ),
    path(
        "contrib/publication/<str:erp_slug>/",
        views.contrib_publication,
        name="contrib_publication",
    ),
    path(
        "contrib/completion/<str:erp_slug>/",
        views.contrib_completion_rate,
        name="contrib_completion_rate",
    ),
    ############################################################################
    # Admin stuff
    ############################################################################
    path(
        "admin/password_reset/",
        auth_views.PasswordResetView.as_view(),
        name="admin_password_reset",
    ),
    path(
        "admin/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="admin_password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="admin_password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="admin_password_reset_complete",
    ),
]
