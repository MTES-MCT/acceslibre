# flake8: noqa
import os

import sentry_sdk

from .sentry import custom_traces_sample_rate
from .settings import *

DEBUG = False

PRODUCTION = True
DATAGOUV_DOMAIN = "https://www.data.gouv.fr"
# NOTE: to retrieve resources id: https://www.data.gouv.fr/api/1/datasets/60a528e8b656ce01b4c0c0a6/
DATAGOUV_RESOURCES_ID = "5b0f44f2-e6ea-4a58-874d-6fe364b40342"
DATAGOUV_RESOURCES_WITH_URL_ID = "93ae96a7-1db7-4cb4-a9f1-6d778370b640"

APP_NAME = os.environ.get("APP", "access4all")
ALLOWED_HOSTS = [
    "localhost",
    SITE_HOST,
    f"{APP_NAME}.osc-fr1.scalingo.io",
    "www.acceslibre.info",
]

if SENTRY_DSN is not None:
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sampler=custom_traces_sample_rate,
        send_default_pii=True,
        environment="production-one-off" if IS_ONE_OFF_CONTAINER else "production",
    )


# FIXME: removed because of a nasty bug with dist static assets
STATICFILES_STORAGE = "core.storage.AppStaticFilesStorage"

# https://docs.djangoproject.com/fr/3.1/ref/middleware/#http-strict-transport-security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

BREVO_TEMPLATE_IDS = {
    "draft_deleted": 457,
    "spam_activities_suggestion": 454,
    "spam_activities_suggestion_admin": 455,
    "draft": 139,
    "erp_imported": 271,
    "account_activation": 532,
    "notif_weekly_unpublished": 456,
    "contact_to_admins": 453,
    "contact_receipt": 440,
    "changed_erp_notification": 458,
    "email_change_activation": 439,
    "password_reset": 463,
    "export-results": 498,
    "erp_imported_brevo_matching": 652,
}
BREVO_CONTACT_LIST_IDS = {
    "tally-respondents": 262,
}
REAL_USER_NOTIFICATION = True
