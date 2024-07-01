import requests
from django.conf import settings
from requests.exceptions import JSONDecodeError, Timeout


class MatomoException(Exception):
    pass


def _get_default_payload(source):
    matomo_settings = settings.MATOMO[source.upper()]
    return {
        "module": "API",
        "idSite": matomo_settings["SITE_ID"],
        "period": "day",
        "date": "last30",
        "format": "JSON",
        "token_auth": matomo_settings["TOKEN"],
    }


def _safe_request(payload, source):
    url = settings.MATOMO[source.upper()]["URL"] + "index.php"
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


def get_unique_visitors(*, source):
    payload = _get_default_payload(source)
    payload["method"] = "VisitsSummary.getUniqueVisitors"
    return sum([v for k, v in _safe_request(payload, source).items()])


def get_number_widget_open(*, source):
    payload = _get_default_payload(source)
    payload["method"] = "Events.getAction"
    data = _safe_request(payload, source)
    nb_events = 0
    for day, values in data.items():
        for value in values:
            if value["label"] == "open":
                nb_events += int(value["nb_events"])
    return nb_events
