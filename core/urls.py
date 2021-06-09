from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.contrib.sitemaps import views as sitemap_views
from django.urls import include, path
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView

from auth.forms import CustomRegistrationForm
from auth.views import (
    CustomActivationCompleteView,
    CustomActivationView,
    CustomRegistrationView,
)
from core.sitemaps import SITEMAPS

# from erp.forms import CustomRegistrationForm
# from erp.views import (
#     CustomActivationView,
#     CustomActivationCompleteView,
#     CustomRegistrationView,
# )


SITEMAP_CACHE_TTL = 86400


@user_passes_test(lambda user: user.is_superuser)
def test_sentry(request):
    raise RuntimeError("Sentry error catching test")


urlpatterns = [
    path("", include("erp.urls")),
    path("annuaire/", include("annuaire.urls")),
    path("api/", include("api.urls")),
    path("contact/", include("contact.urls")),
    path("subscription/", include("subscription.urls")),
    path("stats/", include("stats.urls")),
    # django-registration overrides, handling `next` query string param
    path(
        "accounts/activate/complete/",
        CustomActivationCompleteView.as_view(
            template_name="django_registration/activation_complete.html",
        ),
        name="django_registration_activation_complete",
    ),
    path(
        "accounts/activate/<str:activation_key>/",
        CustomActivationView.as_view(),
        name="django_registration_activate",
    ),
    path(
        "accounts/register/",
        CustomRegistrationView.as_view(form_class=CustomRegistrationForm),
        name="django_registration_register",
    ),
    path("accounts/", include("django_registration.backends.activation.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("admin/", admin.site.urls),
    path(
        "sitemap.xml",
        cache_page(SITEMAP_CACHE_TTL)(sitemap_views.index),
        {"sitemaps": SITEMAPS, "sitemap_url_name": "sitemap"},
    ),
    path(
        "sitemap-<section>.xml",
        cache_page(SITEMAP_CACHE_TTL)(sitemap_views.sitemap),
        {"sitemaps": SITEMAPS},
        name="sitemap",
    ),
    # The service worker cannot be in /static because its scope will be limited to /static.
    # Since we want it to have a scope of the full application, we rely on this TemplateView
    # trick to make it work.
    path(
        "sw.js",
        TemplateView.as_view(
            template_name="sw.js",
            content_type="application/javascript",
        ),
        name="sw.js",
    ),
    path("test-sentry", test_sentry),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
