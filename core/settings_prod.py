# flake8: noqa
import os

import sentry_sdk

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
]

if SENTRY_DSN is not None:
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment="production",
    )

# FIXME: removed because of a nasty bug with dist static assets
STATICFILES_STORAGE = "core.storage.AppStaticFilesStorage"

# https://docs.djangoproject.com/fr/3.1/ref/middleware/#http-strict-transport-security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

BREVO_TEMPLATE_IDS = {
    "draft_deleted": 16,
    "vote_down": 79,
    "spam_activities_suggestion": 87,
    "spam_activities_suggestion_admin": 88,
}

REAL_USER_NOTIFICATION = True
