import logging
import requests

from datetime import datetime

from django.conf import settings


logger = logging.getLogger(__name__)


def send(message, attachements=None, tags=None, today=None):
    """Posts a message to Mattermost if the `MATTERMOST_HOOK` setting has been defined.
    Params:
    - `message`: text message
    - `attachements`: a list of `{pretext, text}` dicts describing attachements
    - `tags`: a list of strings to render as Mattermost tags (the # char will be prepended automatically)
    Docs:
    - https://docs.mattermost.com/developer/message-attachments.html
    """
    if not settings.MATTERMOST_HOOK:
        return
    today = today if today else datetime.now()
    datestr = datetime.strftime(today, "%d/%m/%Y à %H:%M:%S")
    default_tags = ["recette" if settings.STAGING else "production"]
    tags = default_tags + tags if isinstance(tags, (tuple, list)) else default_tags
    tags_str = " ".join([f"#{t}" for t in tags])
    json_body = {"text": f"{settings.SITE_HOST} — {datestr}: {message}\n{tags_str}"}
    if attachements:
        json_body["attachments"] = attachements
    try:
        requests.post(settings.MATTERMOST_HOOK, json=json_body)
    except requests.RequestException as err:
        logger.error(f"Error while posting to Mattermost hook: {err}")
