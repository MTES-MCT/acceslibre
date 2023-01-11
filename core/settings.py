import os

import dj_database_url
from django.contrib.messages import constants as message_constants
from django.core.exceptions import ImproperlyConfigured


def get_env_variable(var_name, required=True, type=str):
    if required:
        try:
            return type(os.environ[var_name])
        except TypeError:
            raise ImproperlyConfigured(f"Unable to cast '{var_name}' to {type}.")
        except KeyError:
            raise ImproperlyConfigured(f"The '{var_name}' environment variable must be set.")
    else:
        return os.environ.get(var_name)


TEST = False
STAGING = False
SITE_NAME = "acceslibre"
SITE_HOST = "acceslibre.beta.gouv.fr"
SITE_ROOT_URL = f"https://{SITE_HOST}"
SECRET_KEY = get_env_variable("SECRET_KEY")
DATAGOUV_API_KEY = get_env_variable("DATAGOUV_API_KEY", required=False)
DATAGOUV_DOMAIN = "https://demo.data.gouv.fr"
DATAGOUV_DATASET_ID = "60a528e8b656ce01b4c0c0a6"
DATAGOUV_RESOURCES_ID = "5b0f44f2-e6ea-4a58-874d-6fe364b40342"

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Maps
MAP_SEARCH_RADIUS_KM = 10
# Mapbox
# Note: this is NOT a sensitive information, as this token is exposed on the frontend anyway
MAPBOX_TOKEN = "pk.eyJ1IjoiemVudHV4IiwiYSI6ImNrOG96dGh1eTA3MTUzcHFwYmM1b3ViMDEifQ.Hg-DxcNWCapv8PhApQLf8g"

# Notifications
# number of days to send a ping notification after an erp is created but not published
UNPUBLISHED_ERP_NOTIF_DAYS = 7

# Mattermost hook
MATTERMOST_HOOK = get_env_variable("MATTERMOST_HOOK", required=False)

# Sentry integration
SENTRY_DSN = get_env_variable("SENTRY_DSN", required=False)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = False

# Static files
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, "staticfiles"))
STATIC_URL = "/static/"
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

# Messages

MESSAGE_TAGS = {
    message_constants.DEBUG: "debug",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "danger",
}


# Application definition

INSTALLED_APPS = [
    "admin_auto_filters",
    "django_extensions",
    "import_export",
    "reset_migrations",
    "django_admin_listfilter_dropdown",
    "compte.apps.CompteConfig",
    "erp.apps.ErpConfig",
    "stats.apps.StatsConfig",
    "subscription.apps.SubscriptionConfig",
    "contact.apps.ContactConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django.contrib.postgres",
    "django.contrib.sitemaps",
    "django.contrib.sites",
    "django.contrib.humanize",
    "corsheaders",
    "logentry_admin",
    "django_better_admin_arrayfield.apps.DjangoBetterAdminArrayfieldConfig",
    "rest_framework",
    "rest_framework_gis",
    "crispy_forms",
    "waffle",
    "reversion",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "waffle.middleware.WaffleMiddleware",
    "stats.middleware.TrackStatsWidget",
]

SITE_ID = 1

CORS_ORIGIN_ALLOW_ALL = True

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10/second",
        "user": "10/second",
    },
}

ROOT_URLCONF = "core.urls"


def expose_site_context(request):
    """Expose generic site related static values to all templates.

    Note: we load these values from django.conf.settings so we can retrieve
    those defined/overriden in env-specific settings module (eg. dev/prod).
    """
    from django.conf import settings

    return {
        "MAP_SEARCH_RADIUS_KM": settings.MAP_SEARCH_RADIUS_KM,
        "MAPBOX_TOKEN": settings.MAPBOX_TOKEN,
        "SENTRY_DSN": settings.SENTRY_DSN,
        "SITE_NAME": settings.SITE_NAME,
        "SITE_HOST": settings.SITE_HOST,
        "SITE_ROOT_URL": settings.SITE_ROOT_URL,
        "STAGING": settings.STAGING,
    }


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": False,
            "context_processors": [
                "core.settings.expose_site_context",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Database connection
# see https://docs.djangoproject.com/en/3.0/ref/settings/#databases
# see https://doc.scalingo.com/languages/python/django/start#configure-the-database-access
# see https://pypi.org/project/dj-database-url/ for options management
database_url = os.environ.get("DATABASE_URL", "postgres://access4all:access4all@localhost/access4all")
DATABASES = {"default": dj_database_url.config()}
DATABASES["default"]["ENGINE"] = "django.contrib.gis.db.backends.postgis"

# Default field to use for implicit model primary keys
# see https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Cookie security
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "fr"
TIME_ZONE = "Europe/Paris"
DATETIME_FORMAT = "Y-m-d, H:i:s"
USE_I18N = True
USE_L10N = False
USE_TZ = True

# Crispy forms

CRISPY_TEMPLATE_PACK = "bootstrap4"

# Email configuration (production uses Mailjet - see README)

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST = get_env_variable("EMAIL_HOST")
EMAIL_PORT = get_env_variable("EMAIL_PORT", type=int)
EMAIL_HOST_USER = get_env_variable("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = get_env_variable("EMAIL_HOST_PASSWORD")
DEFAULT_EMAIL = "acceslibre@beta.gouv.fr"
DEFAULT_FROM_EMAIL = f"L'équipe {SITE_NAME} <{DEFAULT_EMAIL}>"
MANAGERS = [("Acceslibre", DEFAULT_EMAIL)]
EMAIL_FILE_PATH = "/tmp/django_emails"
EMAIL_SUBJECT_PREFIX = f"[{SITE_NAME}]"
EMAIL_USE_LOCALTIME = True

LOGIN_URL = "/compte/login/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_REDIRECT_URL = "/"
ACCOUNT_ACTIVATION_DAYS = 7
EMAIL_ACTIVATION_DAYS = 1
REGISTRATION_OPEN = True
REGISTRATION_SALT = "a4a-registration"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "compte.auth.EmailOrUsernameModelBackend",
)

# graphviz
GRAPH_MODELS = {
    "all_applications": True,
    "group_models": True,
}

# Usernames blacklist
USERNAME_BLACKLIST = [
    # English/generic
    "anon",
    "anonym",
    "anonymous",
    "abuse",
    "admin",
    "administrator",
    "contact",
    "deleted",
    "error",
    "ftp",
    "hostmaster",
    "info",
    "is",
    "it",
    "list",
    "list-request",
    "mail",
    "majordomo",
    "marketing",
    "mis",
    "press",
    "mail",
    "media",
    "moderator",
    "news",
    "noc",
    "postmaster",
    "reporting",
    "root",
    "sales",
    "security",
    "ssl-admin",
    "ssladmin",
    "ssladministrator",
    "sslwebmaster",
    "security",
    "support",
    "sysadmin",
    "trouble",
    "usenet",
    "uucp",
    "webmaster",
    "www",
    # French
    "abus",
    "aide",
    "administrateur",
    "anonyme",
    "commercial",
    "courriel",
    "email",
    "erreur",
    "information",
    "moderateur",
    "presse",
    "rapport",
    "securite",
    "sécurité",
    "service",
    "signalement",
    "television",
    "tv",
    "vente",
    "webmestre",
]
