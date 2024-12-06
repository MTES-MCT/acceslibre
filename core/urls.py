from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.contrib.sitemaps import views as sitemap_views
from django.urls import include, path
from django.views.decorators.cache import cache_page
from django.views.generic import RedirectView
from django.views.i18n import JavaScriptCatalog

from compte.forms import CustomAuthenticationForm, CustomRegistrationForm
from compte.views import (
    CustomActivationCompleteView,
    CustomActivationView,
    CustomPasswordResetView,
    CustomRegistrationCompleteView,
    CustomRegistrationView,
)
from core.sitemaps import SITEMAPS
from core.views import robots_txt

# in seconds
ONE_HOUR = 60 * 60
ONE_DAY = 24 * ONE_HOUR

urlpatterns = [
    path(
        "librairie",
        RedirectView.as_view(url="https://startupdetat.typeform.com/to/XjPdaMBE", permanent=True),
    ),
    path("", include("erp.urls")),
    path("annuaire/", include("annuaire.urls")),
    path("api/", include("api.urls")),
    path("contact/", include("contact.urls")),
    path("subscription/", include("subscription.urls")),
    path("stats/", include("stats.urls")),
    # django-registration overrides, handling `next` query string param
    path(
        "compte/activate/complete/",
        CustomActivationCompleteView.as_view(
            template_name="django_registration/activation_complete.html",
        ),
        name="django_registration_activation_complete",
    ),
    path("compte/activate/", CustomActivationView.as_view(), name="django_registration_activate"),
    path(
        "compte/register/",
        CustomRegistrationView.as_view(form_class=CustomRegistrationForm),
        name="django_registration_register",
    ),
    path(
        "compte/register/complete/",
        CustomRegistrationCompleteView.as_view(template_name="django_registration/registration_complete.html"),
        name="django_registration_complete",
    ),
    path("compte/login/", LoginView.as_view(form_class=CustomAuthenticationForm), name="login"),
    path("compte/password_reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    # TODO more things to move to auth
    path("compte/", include("django_registration.backends.activation.urls")),
    path("compte/", include("django.contrib.auth.urls")),
    path("compte/", include("compte.urls")),
    path("admin/", admin.site.urls),
    path("two_factor/", include(("admin_two_factor.urls", "admin_two_factor"), namespace="two_factor")),
    path(
        "sitemap.xml", cache_page(ONE_DAY)(sitemap_views.index), {"sitemaps": SITEMAPS, "sitemap_url_name": "sitemap"}
    ),
    path("sitemap-<section>.xml", cache_page(ONE_DAY)(sitemap_views.sitemap), {"sitemaps": SITEMAPS}, name="sitemap"),
    path("maintenance-mode/", include("maintenance_mode.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("jsi18n/", cache_page(ONE_HOUR, key_prefix="jsi18n")(JavaScriptCatalog.as_view()), name="javascript-catalog"),
    path("robots.txt", robots_txt),
]
if "rosetta" in settings.INSTALLED_APPS:
    urlpatterns += [path("rosetta/", include("rosetta.urls"))]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
