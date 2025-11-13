# flake8: noqa
from .settings import *

DEBUG = True

SITE_HOST = "127.0.0.1"
SITE_ROOT_URL = f"http://{SITE_HOST}:8000"

ALLOWED_HOSTS = [
    SITE_HOST,
    "127.0.0.1",
    "127.0.0.1:8000",
    "localhost",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS.append("debug_toolbar.apps.DebugToolbarConfig")
INSTALLED_APPS.append("rosetta")
INSTALLED_APPS.append("django_deep_translator")

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

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
