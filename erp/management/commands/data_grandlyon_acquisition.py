from collections import defaultdict

import requests
from django.core.management.base import BaseCommand

from erp.exceptions import PermanentlyClosedException
from erp.models import Activite, Erp
from erp.provider import geocoder


class Command(BaseCommand):
    help = "Import data from GrandLyon datasets"

    def _ensure_not_permanently_closed(self, qs):
        if any([erp.permanently_closed for erp in qs]):
            raise PermanentlyClosedException()

    def _set_sound_beacon(self):
        url = "https://data.grandlyon.com/fr/datapusher/ws/grandlyon/car_care.balise_sonore_erp/all.json?maxfeatures=-1"
        response = requests.get(url)
        if response.status_code != 200:
            print("Non 200 response, exiting")
            return

        response = response.json().get("values", [])
        matches = defaultdict(int)
        for result in response:
            obj = {}
            obj["nom"] = result["denomination"]
            obj["commune"] = result["commune"]
            obj["adresse"] = result["adresse"]

            obj["adresse"] = f"{obj['adresse']}, {obj['commune']}"

            print(f"Managing {obj['nom']}, {obj['adresse']} {obj['commune']}")

            locdata = geocoder.geocode(obj["adresse"])
            for key in ("numero", "voie", "lieu_dit", "code_postal", "commune"):
                obj[key] = locdata.get(key)

            activity = None
            if "collège" in obj["nom"].lower():
                activity = Activite.objects.get(nom="Collège")

            erp = None
            if activity:
                erps = Erp.objects.find_duplicate(
                    numero=obj.get("numero"),
                    commune=obj["commune"],
                    activite=activity,
                    voie=obj.get("voie"),
                    lieu_dit=obj.get("lieu_dit"),
                )
                try:
                    self._ensure_not_permanently_closed(erps)
                except PermanentlyClosedException:
                    continue
                erp = erps.first()

            if not erp:
                erps = (
                    Erp.objects.nearest(point=locdata["geom"], max_radius_km=0.075)
                    .filter(nom__lower__in=(obj["nom"].lower(), obj["nom"].lower().replace("-", " ")))
                    .first()
                )
                try:
                    self._ensure_not_permanently_closed(erps)
                except PermanentlyClosedException:
                    continue
                erp = erps.first()

            if not erp:
                print("Not found on acceslibre, skipping...")
                matches["not_found"] += 1
                continue

            erp.accessibilite.entree_balise_sonore = True
            erp.accessibilite.save()
            print(f"entree_balise_sonore set on {erp.nom}")
            matches["found"] += 1

        print(matches)

    def handle(self, *args, **options):
        self._set_sound_beacon()
