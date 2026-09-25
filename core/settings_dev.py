# flake8: noqa
from urllib.parse import urlparse

from .settings import *

DEBUG = True

SITE_ROOT_URL = os.environ.get("SITE_ROOT_URL", "http://127.0.0.1:8000")
SITE_HOST = urlparse(SITE_ROOT_URL).hostname
CORS_ALLOWED_ORIGINS = [SITE_ROOT_URL]
REQUIRE_2FA = False

ALLOWED_HOSTS = [
    SITE_HOST,
    "127.0.0.1",
    "127.0.0.1:7000",
    "localhost",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS.append("django_extensions")
INSTALLED_APPS.append("rosetta")
INSTALLED_APPS.append("django_deep_translator")

if USE_DEBUG_TOOLBAR:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
    # Hack to display the debug toolbar if using django through the docker container
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: True,
    }

TEMPLATES[0]["OPTIONS"]["debug"] = True
TEMPLATES[0]["OPTIONS"]["context_processors"].insert(0, "django.template.context_processors.debug")

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

LOGGING = {
    "version": 1,
    "handlers": {
        "console": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        }
    },
    "loggers": {},
}
SQL_LOGS = False
if SQL_LOGS:
    LOGGING["loggers"] = {
        "django.db.backends": {
            "level": "DEBUG",
            "handlers": ["console"],
        }
    }

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

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_STORE_EAGER_RESULT = True

PARCEL_HMR_PORT = 34471
CONTENT_SECURITY_POLICY["DIRECTIVES"]["connect-src"] = [
    *CONTENT_SECURITY_POLICY["DIRECTIVES"]["connect-src"],
    f"ws://127.0.0.1:{PARCEL_HMR_PORT}",
    f"ws://localhost:{PARCEL_HMR_PORT}",
]
