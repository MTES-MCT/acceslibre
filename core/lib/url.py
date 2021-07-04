from urllib.parse import urlencode


def encode_qs(**kwargs):
    "Generate URL query string parameters ensuring None values are encoded as an empty string."
    params = {}
    for key, value in kwargs.items():
        params[key] = value if value not in (None, "None") else ""
    return "?" + urlencode(params)
