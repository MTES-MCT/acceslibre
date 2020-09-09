from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from erp.forms import CustomRegistrationForm
from erp.views import (
    CustomActivationView,
    CustomActivationCompleteView,
    CustomRegistrationView,
)


urlpatterns = [
    path("", include("erp.urls")),
    path("api/", include("api.urls")),
    path("contact/", include("contact.urls")),
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
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls)),] + urlpatterns
