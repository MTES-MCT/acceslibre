# flake8: noqa

import sentry_sdk

from .settings import *

STAGING = True
SITE_NAME = "acceslibre (recette)"
SITE_HOST = "recette.acceslibre.info"
SITE_ROOT_URL = f"https://{SITE_HOST}"
ALLOWED_HOSTS = [SITE_HOST, "recette.acceslibre.info"]

if SENTRY_DSN is not None:
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                cache_spans=True,
            ),
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        before_send=keep_only_username,
        environment="one-off-recette" if IS_ONE_OFF_CONTAINER else "recette",
    )

# FIXME: removed because of a nasty bug with dist static assets
STATICFILES_STORAGE = "core.storage.AppStaticFilesStorage"

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
