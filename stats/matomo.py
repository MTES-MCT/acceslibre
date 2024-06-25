import requests
from django.conf import settings
from requests.exceptions import JSONDecodeError, Timeout


class MatomoException(Exception):
    pass


def _get_default_payload():
    return {
        "module": "API",
        "idSite": settings.MATOMO["SITE_ID"],
        "period": "day",
        "date": "last30",
        "format": "JSON",
        "token_auth": settings.MATOMO["TOKEN"],
    }


def _safe_request(payload):
    url = settings.MATOMO["URL"] + "index.php"
    try:
        response = requests.post(url, data=payload, timeout=2)
    except Timeout:
        raise MatomoException

    if not response.status_code == 200:
        raise MatomoException

    try:
        return response.json()
    except JSONDecodeError:
        raise MatomoException


def get_unique_visitors():
    payload = _get_default_payload()
    payload["method"] = "VisitsSummary.getUniqueVisitors"
    return sum([v for k, v in _safe_request(payload).items()])


def get_number_widget_open():
    payload = _get_default_payload()
    payload["method"] = "Events.getAction"
    data = _safe_request(payload)
    nb_events = 0
    for day, values in data.items():
        for value in values:
            if value["label"] == "open":
                nb_events += int(value["nb_events"])
    return nb_events
