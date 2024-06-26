# flake8: noqa
from .settings import *

DEBUG = True
TEST = True

SITE_HOST = "localhost"
SITE_ROOT_URL = "http://testserver"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = []
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []


TEMPLATES[0]["OPTIONS"]["debug"] = True
TEMPLATES[0]["OPTIONS"]["context_processors"].insert(0, "django.template.context_processors.debug")

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_STORE_EAGER_RESULT = True

BREVO_TEMPLATE_IDS = {}
BREVO_CONTACT_LIST_IDS = {}

MATOMO["TOKEN"] = "XXXX"
