# flake8: noqa
import os

import sentry_sdk

from .settings import *

DEBUG = False

DATAGOUV_DOMAIN = "https://www.data.gouv.fr"

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
