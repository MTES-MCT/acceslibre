# flake8: noqa

import sentry_sdk

from .settings import *

STAGING = True
SITE_NAME = "acceslibre (recette)"
SITE_HOST = "recette.acceslibre.info"
SITE_ROOT_URL = f"https://{SITE_HOST}"
ALLOWED_HOSTS = [SITE_HOST, "recette.acceslibre.info", "recette-access4all-pr2078.osc-fr1.scalingo.io"]
ADMIN_TWO_FACTOR_NAME = SITE_NAME

if SENTRY_DSN is not None:
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment="one-off-recette" if IS_ONE_OFF_CONTAINER else "recette",
    )

# FIXME: removed because of a nasty bug with dist static assets
STATICFILES_STORAGE = "core.storage.AppStaticFilesStorage"

# https://docs.djangoproject.com/fr/3.1/ref/middleware/#http-strict-transport-security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 3600

BREVO_TEMPLATE_IDS = {
    "draft_deleted": 27,
    "spam_activities_suggestion": 24,
    "spam_activities_suggestion_admin": 25,
    "draft": 8,
    "erp_imported": 9,
    "account_activation": 34,
    "notif_weekly_unpublished": 26,
    "contact_to_admins": 35,
    "contact_receipt": 21,
    "changed_erp_notification": 28,
    "email_change_activation": 22,
    "password_reset": 29,
    "export-results": 33,
    "erp_imported_brevo_matching": 36,
}
BREVO_CONTACT_LIST_IDS = {
    "tally-respondents": 11,
}
