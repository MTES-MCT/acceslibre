import requests

API_URL = "https://api.panoramax.xyz/api/search"
HEADERS = {"accept": "application/json"}


def get_image_id(lat, lon, distance="3-15"):
    params = {
        "place_position": f"{lon},{lat}",
        "limit": 1,
        "place_distance": distance,
    }
    r = requests.get(API_URL, params=params, headers=HEADERS, timeout=5)
    r.raise_for_status()
    data = r.json()
    if data.get("features"):
        return data["features"][0]["id"]
    return None
