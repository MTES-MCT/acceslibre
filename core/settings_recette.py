# flake8: noqa
import os

import sentry_sdk

from .settings import *

STAGING = True
SITE_NAME = "acceslibre (recette)"
SITE_HOST = "recette-access4all.osc-fr1.scalingo.io"
SITE_ROOT_URL = f"https://{SITE_HOST}"
ALLOWED_HOSTS = [SITE_HOST]

if SENTRY_DSN is not None:
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment="recette",
    )

# FIXME: removed because of a nasty bug with dist static assets
STATICFILES_STORAGE = "core.storage.AppStaticFilesStorage"

# https://docs.djangoproject.com/fr/3.1/ref/middleware/#http-strict-transport-security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 3600

SEND_IN_BLUE_TEMPLATE_IDS = {
    "draft_deleted": 4,
}
