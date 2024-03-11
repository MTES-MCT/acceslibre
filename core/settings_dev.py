# flake8: noqa
from .settings import *

DEBUG = True

SITE_HOST = "127.0.0.1"
SITE_ROOT_URL = f"http://{SITE_HOST}:8000"

ALLOWED_HOSTS = [
    SITE_HOST,
    "127.0.0.1",
    "localhost",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS.append("debug_toolbar")
INSTALLED_APPS.append("rosetta")
ROSETTA_POFILE_WRAP_WIDTH = 0

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
    "draft_deleted": 4,
    "spam_activities_suggestion": 6,
    "spam_activities_suggestion_admin": 7,
    "draft": 8,
    "erp_imported": 9,
    "account_activation": 10,
    "notif_weekly_unpublished": 11,
    "contact_to_admins": 12,
    "contact_receipt": 13,
    "changed_erp_notification": 14,
    "email_change_activation": 15,
    "password_reset": 17,
}


CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_STORE_EAGER_RESULT = True
