from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from django_registration.backends.activation.views import RegistrationView

from erp.forms import CustomRegistrationForm

urlpatterns = [
    path("", include("erp.urls")),
    path("api/", include("api.urls")),
    path("stats/", include("stats.urls")),
    path(
        "accounts/register/",
        RegistrationView.as_view(form_class=CustomRegistrationForm),
        name="django_registration_register",
    ),
    path("accounts/", include("django_registration.backends.activation.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("contactez-nous/", include("contact_form.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls)),] + urlpatterns
