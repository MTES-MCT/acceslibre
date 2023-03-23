# flake8: noqa
from .settings import *

DEBUG = True

SITE_HOST = "127.0.0.1"
SITE_ROOT_URL = f"http://{SITE_HOST}:8000"

ALLOWED_HOSTS = [
    SITE_HOST,
    "127.0.0.1",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS.append("debug_toolbar")
INSTALLED_APPS.append("rosetta")

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

TEMPLATES[0]["OPTIONS"]["debug"] = True
TEMPLATES[0]["OPTIONS"]["context_processors"].insert(0, "django.template.context_processors.debug")

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}


SEND_IN_BLUE_TEMPLATE_IDS = {
    "draft_deleted": 4,
    "vote_down": 5,
}


CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_STORE_EAGER_RESULT = True
