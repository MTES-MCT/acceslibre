# flake8: noqa
from .settings import *


DEBUG = True

SITE_HOST = "localhost"
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

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache",}}
# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#         "LOCATION": "cache_acceslibre",
#     }
# }

TEMPLATES[0]["OPTIONS"]["debug"] = True
TEMPLATES[0]["OPTIONS"]["context_processors"].insert(
    0, "django.template.context_processors.debug"
)

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler",},},
    "root": {"handlers": ["console"], "level": "DEBUG",},
}
