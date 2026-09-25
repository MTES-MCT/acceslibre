from django.conf import settings
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth import REDIRECT_FIELD_NAME, login
from django.contrib.auth.views import redirect_to_login
from django.contrib.sitemaps import views as sitemap_views
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, resolve_url
from django.urls import include, path, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import cache_page
from django.views.generic import RedirectView
from django.views.i18n import JavaScriptCatalog
from two_factor.admin import AdminSiteOTPRequired, AdminSiteOTPRequiredMixin
from two_factor.urls import urlpatterns as tf_urls
from two_factor.views import LoginView as TwoFactorLoginView

from compte.forms import CustomAuthenticationForm, CustomRegistrationForm
from compte.views import (
    CustomActivationCompleteView,
    CustomActivationView,
    CustomLoginView,
    CustomPasswordResetView,
    CustomRegistrationCompleteView,
    CustomRegistrationView,
)
from core.sitemaps import SITEMAPS
from core.views import html_sitemap, robots_txt


class CustomAdminSiteOTPRequired(AdminSiteOTPRequired):
    def has_permission(self, request):
        if not settings.REQUIRE_2FA:
            return AdminSite.has_permission(self, request)
        return super().has_permission(request)

    def login(self, request, extra_context=None):
        redirect_to = request.POST.get(REDIRECT_FIELD_NAME, request.GET.get(REDIRECT_FIELD_NAME))
        if request.method == "GET" and super(AdminSiteOTPRequiredMixin, self).has_permission(request):
            if not settings.REQUIRE_2FA or request.user.is_verified():
                index_path = reverse("admin:index", current_app=self.name)
            else:
                index_path = reverse("two_factor:setup", current_app=self.name)
            return HttpResponseRedirect(index_path)

        if not redirect_to or not url_has_allowed_host_and_scheme(url=redirect_to, allowed_hosts=[request.get_host()]):
            redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

        return redirect_to_login(redirect_to, login_url=settings.ADMIN_LOGIN_URL)


class CustomTwoFactorLoginView(TwoFactorLoginView):
    """
    Two-factor login wizard that skips the OTP token step entirely when
    REQUIRE_2FA is disabled (used on local dev environments).
    """

    def has_token_step(self):
        if not settings.REQUIRE_2FA:
            return False
        return super().has_token_step()

    def has_backup_step(self):
        if not settings.REQUIRE_2FA:
            return False
        return super().has_backup_step()

    def done(self, form_list, **kwargs):
        if not settings.REQUIRE_2FA:
            login(self.request, self.get_user())
            return redirect(self.get_success_url())
        return super().done(form_list, **kwargs)

    # The parent class stores the original method objects in condition_dict, so
    # we must re-bind it here for our overrides to be taken into account.
    condition_dict = {
        TwoFactorLoginView.TOKEN_STEP: has_token_step,
        TwoFactorLoginView.BACKUP_STEP: has_backup_step,
    }


# Replace the default two-factor login view so that it honours REQUIRE_2FA.
tf_urlpatterns = []
for tf_pattern in tf_urls[0]:
    if getattr(tf_pattern, "name", None) == "login":
        tf_urlpatterns.append(path("account/login/", CustomTwoFactorLoginView.as_view(), name="login"))
    else:
        tf_urlpatterns.append(tf_pattern)
tf_urls = (tf_urlpatterns, "two_factor")


admin.site.__class__ = CustomAdminSiteOTPRequired
# in seconds
ONE_HOUR = 60 * 60
ONE_DAY = 24 * ONE_HOUR
urlpatterns = [
    path(
        "librairie",
        RedirectView.as_view(url="https://startupdetat.typeform.com/to/XjPdaMBE", permanent=True),
    ),
    # Must come before erp.urls: `recherche/<str:commune_slug>/` would shadow
    # `recherche/erps/` otherwise.
    path("", include("api.frontend_urls")),
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
    path("compte/login/", CustomLoginView.as_view(form_class=CustomAuthenticationForm), name="login"),
    path("compte/password_reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    # TODO more things to move to auth
    path("compte/", include("django_registration.backends.activation.urls")),
    path("compte/", include("django.contrib.auth.urls")),
    path("compte/", include("compte.urls")),
    path("", include(tf_urls)),
    path("admin/", admin.site.urls),
    path(
        "sitemap.xml", cache_page(ONE_DAY)(sitemap_views.index), {"sitemaps": SITEMAPS, "sitemap_url_name": "sitemap"}
    ),
    path("sitemap-<section>.xml", cache_page(ONE_DAY)(sitemap_views.sitemap), {"sitemaps": SITEMAPS}, name="sitemap"),
    path("plan-du-site/", html_sitemap, name="html_sitemap"),
    path("maintenance-mode/", include("maintenance_mode.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("jsi18n/", cache_page(ONE_HOUR, key_prefix="jsi18n")(JavaScriptCatalog.as_view()), name="javascript-catalog"),
    path("robots.txt", robots_txt),
]
if "rosetta" in settings.INSTALLED_APPS:
    urlpatterns += [path("rosetta/", include("rosetta.urls"))]

if settings.DEBUG and settings.USE_DEBUG_TOOLBAR:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
