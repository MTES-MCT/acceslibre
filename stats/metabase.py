import requests
from django.conf import settings
from requests.exceptions import JSONDecodeError, Timeout
from datetime import datetime

card_ids = {
    "total_erps": 458,
    "last_30_days_active_contributors": 351,
    "average_completion_rate": 325,
    "last_12_months_created_or_updated_erps": 423,
    "erp_completion_totals": 355,
}


class MetabaseException(Exception):
    pass


def _safe_request(card_id: int, timeout: int = 2):
    url = f"{settings.METABASE['URL']}card/{card_id}/query"
    headers = {
        "x-api-key": settings.METABASE["TOKEN"],
    }

    try:
        response = requests.post(url, timeout=timeout, headers=headers)
    except Timeout:
        raise MetabaseException
    if not response.status_code == 202:
        raise MetabaseException
    try:
        response_json = response.json()
        return response_json["data"]["rows"]
    except JSONDecodeError:
        raise MetabaseException


def get_total_erps():
    total_erps = _safe_request(card_ids["total_erps"])
    processed_erps = sorted(
        [(datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ"), value) for date_str, value in total_erps],
        reverse=True,
        key=lambda x: x[0],
    )
    return processed_erps


def get_last_30_days_active_contributors():
    return _safe_request(card_ids["last_30_days_active_contributors"])


def get_average_completion_rate():
    try:
        average_completion_rate = _safe_request(card_ids["average_completion_rate"])
        average_completion_rate = average_completion_rate[0][0]
        return f"{average_completion_rate:.2f}%"
    except Exception as e:
        raise MetabaseException(e)


def get_last_12_months_created_or_updated_erps():
    try:
        last_12_months_created_or_updated_erps = _safe_request(card_ids["last_12_months_created_or_updated_erps"], 8)
        last_12_months_created_or_updated_erps = last_12_months_created_or_updated_erps[0][0]
        return f"{last_12_months_created_or_updated_erps:.2f}%"
    except Exception as e:
        raise MetabaseException(e)


def get_erp_completion_totals():
    return _safe_request(card_ids["erp_completion_totals"])
