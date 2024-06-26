import os

import environ
from corsheaders.defaults import default_headers
from django.contrib.messages import constants as message_constants
from django.utils.translation import gettext_lazy as trans

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# Set the project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


TEST = False
STAGING = False
PRODUCTION = False
IS_ONE_OFF_CONTAINER = os.environ.get("CONTAINER", "").startswith("one-off")
SITE_NAME = "acceslibre"
SITE_HOST = "acceslibre.beta.gouv.fr"
SITE_ROOT_URL = f"https://{SITE_HOST}"
SECRET_KEY = env("SECRET_KEY")
DATAGOUV_API_KEY = env("DATAGOUV_API_KEY", default=None)
DATAGOUV_DOMAIN = "https://demo.data.gouv.fr"
DATAGOUV_DATASET_ID = "60a528e8b656ce01b4c0c0a6"
# NOTE: to retrieve resources id: https://demo.data.gouv.fr/api/1/datasets/60a528e8b656ce01b4c0c0a6/
DATAGOUV_RESOURCES_ID = "993e8f0f-07fe-4b44-8fba-cca4ce102c0c"
DATAGOUV_RESOURCES_WITH_URL_ID = "93ae96a7-1db7-4cb4-a9f1-6d778370b640"
ADMIN_TWO_FACTOR_NAME = SITE_NAME

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

CSP_DEFAULT_SRC = (
    "'self'",
    "data:",  # used for Leaflet CenterCross plugin.
    "*.mapbox.com",
    "*.gouv.fr",
    "*.incubateur.net",
    "acceslibre.matomo.cloud",
    "*.tile.openstreetmap.org",
    "client.crisp.chat",
    "image.crisp.chat",
    "storage.crisp.chat",
    "game.crisp.chat",
    "wss://client.relay.crisp.chat",
    "wss://stream.relay.crisp.chat",
    "*.acceslibre.info",
)

CSP_EXCLUDE_URL_PREFIXES = ("/api", "/admin")  # swagger and admin uses scripts from remote cdns

# Maps
MAP_SEARCH_RADIUS_KM = 10

MAP_DEFAULT_ZOOM = 6
MAP_DEFAULT_ZOOM_LARGE_CITY = 12
MAP_DEFAULT_ZOOM_STREET = 15
MAP_DEFAULT_ZOOM_HOUSENUMBER = 17

# Mapbox
# NOTE: this is NOT a sensitive information, as this token is exposed on the frontend anyway
MAPBOX_TOKEN = "pk.eyJ1IjoiYWNjZXNsaWJyZSIsImEiOiJjbGVyN2p0cW8wNzBoM3duMThhaGY4cTRtIn0.jEdq_xNlv-oBu_q_UAmkxw"

# Notifications
# Whether we send real email notifications
REAL_USER_NOTIFICATION = False
# number of days to send a ping notification after an erp is created but not published
UNPUBLISHED_ERP_NOTIF_DAYS = 7

# Mattermost hook
MATTERMOST_HOOK = env("MATTERMOST_HOOK", default=None)

# Sentry integration
SENTRY_DSN = env("SENTRY_DSN", default=None)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Source: https://github.com/chucknorris-io/swear-words/blob/master/fr completed with some plurals
FRENCH_PROFANITY_WORDLIST = os.path.join(BASE_DIR, "erp/provider/french_profanity_wordlist.txt")
# For each user, we ignore the first <NB_PROFANITIES_IGNORED> profanities in free texts, after that,
# the user account is deactivated
NB_PROFANITIES_IGNORED = 1

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
    "django_admin_listfilter_dropdown",
    "compte.apps.CompteConfig",
    "erp.apps.ErpConfig",
    "stats.apps.StatsConfig",
    "subscription.apps.SubscriptionConfig",
    "contact.apps.ContactConfig",
    "modeltranslation",
    "admin_two_factor.apps.TwoStepVerificationConfig",
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
    "rest_framework_api_key",
    "rest_framework_gis",
    "crispy_forms",
    "waffle",
    "reversion",
    "maintenance_mode",
]


MIDDLEWARE = [
    "csp.middleware.CSPMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "waffle.middleware.WaffleMiddleware",
    "stats.middleware.TrackStatsWidget",
    "maintenance_mode.middleware.MaintenanceModeMiddleware",
]


SITE_ID = 1

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = (
    *default_headers,
    "X-OriginUrl",
)


REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "3/second",
        "user": "3/second",
    },
    "DEFAULT_PERMISSION_CLASSES": [
        "api.permissions.IsAllowedForAction",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "api.renderers.GeoJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

INTERNAL_API_KEY_NAME = "acceslibre - internal uses only"

ROOT_URLCONF = "core.urls"


def expose_site_context(request):
    """Expose generic site related static values to all templates.

    Note: we load these values from django.conf.settings so we can retrieve
    those defined/overriden in env-specific settings module (eg. dev/prod).
    """
    from django.conf import settings

    return {
        "MAP_SEARCH_RADIUS_KM": settings.MAP_SEARCH_RADIUS_KM,
        "SENTRY_DSN": settings.SENTRY_DSN,
        "SITE_NAME": settings.SITE_NAME,
        "SITE_ROOT_URL": settings.SITE_ROOT_URL,
        "STAGING": settings.STAGING or settings.DEBUG,
        "MAP_DEFAULT_ZOOM": settings.MAP_DEFAULT_ZOOM,
        "MAP_DEFAULT_ZOOM_LARGE_CITY": settings.MAP_DEFAULT_ZOOM_LARGE_CITY,
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
                "django.template.context_processors.i18n",
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
DATABASES = {
    "default": env.db(),
}
DATABASES["default"]["ENGINE"] = "django.contrib.gis.db.backends.postgis"

# Default field to use for implicit model primary keys
# see https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

CACHES = {
    "default": env.cache_url("SCALINGO_REDIS_URL"),
}

CELERY_BROKER_URL = CACHES["default"]["LOCATION"]
CELERY_RESULT_BACKEND = CACHES["default"]["LOCATION"]

# Cookie security
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "fr"
LANGUAGES = [
    ("fr", trans("French")),
    ("en", trans("English")),
]
LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)
TIME_ZONE = "Europe/Paris"
DATETIME_FORMAT = "Y-m-d, H:i:s"
USE_I18N = True
USE_L10N = True
USE_TZ = True
DEEPL_AUTH_KEY = env("DEEPL_AUTH_KEY", default=None)
DEEPL_LANGUAGES = {"EN_GB": "en"}
DEEPL_MAPPING = {"en": "EN-GB"}

OUTSCRAPER_API_KEY = env("OUTSCRAPER_API_KEY", default=None)
SCRAPFLY_IO_API_KEY = env("SCRAPFLY_IO_API_KEY", default=None)
# Crispy forms
CRISPY_TEMPLATE_PACK = "bootstrap4"

# Email configuration (production uses Mailjet - see README)
BREVO_API_KEY = env("BREVO_API_KEY")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_EMAIL = "support@acceslibre.beta.gouv.fr"
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

MIN_NB_ANSWERS_IN_CONTRIB = 3  # 3 + entree_porte_presence

# https://adresse.data.gouv.fr/api-doc/adresse
ADRESSE_DATA_GOUV_SEARCH_TYPE_CITY = "municipality"
ADRESSE_DATA_GOUV_SEARCH_TYPE_HOUSENUMBER = "housenumber"
ADRESSE_DATA_GOUV_SEARCH_TYPE_STREET = "street"
IN_MUNICIPALITY_SEARCH_TYPE = "in_municipality"

MATOMO = {"URL": "https://acceslibre.matomo.cloud/", "SITE_ID": 1, "TOKEN": env("MATOMO_API_TOKEN", default=None)}
