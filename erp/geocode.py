GEOCODER_URL = "https://api-adresse.data.gouv.fr/search/"


def geocode(erp, adresse):
    # retrieve geolocoder data
    r = requests.get(GEOCODER_URL, {"q": adresse})
    if r.status_code != 200:
        return
    data = r.json()
    try:
        features = data["features"]
        if len(features) == 0:
            return
        feature = data["features"][0]
        print(json.dumps(feature, indent=2))
        # coordinates
        geometry = feature["geometry"]
        erp.lat = geometry["coordinates"][1]
        erp.lat = geometry["coordinates"][0]
        # address
        properties = feature["properties"]
        erp.num = properties["housenumber"]
        # erp.cplt = properties[""]
        erp.voie = properties["street"]
        # erp.lieu_dit = properties[""]
        erp.cpost = properties["postcode"]
        erp.commune = properties["city"]
        erp.code_insee = properties["citycode"]
        print("all fine")
    except (KeyError, IndexError) as err:
        # print(json.dumps(data, indent=2))
        raise ValidationError({"adresse": f"Impossible de géocoder l'adresse '{adresse}': {err}."})
