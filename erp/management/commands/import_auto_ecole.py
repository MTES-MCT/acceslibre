import csv

import requests
import reversion
from django.core.management.base import BaseCommand
from rest_framework.exceptions import ValidationError

from erp.imports.serializers import ErpImportSerializer
from erp.models import Activite, Erp, ExternalSource
from erp.provider.geocoder import geocode
from django.db import IntegrityError


class Command(BaseCommand):
    help = "Download the CSV file of handicap-friendly driving schools."

    url = "https://autoecoles.securite-routiere.gouv.fr/sites/default/files/handicap-schools/auto-ecoles-handicap.csv"

    def handle(self, *args, **kwargs):
        self.stdout.write(f"Downloading file from {self.url}...")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/csv,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

        response = requests.get(self.url, headers=headers)

        content = response.content.decode("utf-8-sig").splitlines()
        reader = csv.DictReader(content, delimiter=";")

        next(reader, None)  # Skip the header row
        # NOTE headers are ['Départ.', 'Sourds ou malentendants', 'Handicap locomoteur', 'N° Agrément', 'Raison sociale', 'Enseigne', 'Adresse ', 'Adresse suite', 'CP', 'Ville']

        activity = Activite.objects.get(slug="auto-ecole")
        for row in reader:
            if "Adresse " not in row:
                print(f"ERP without address, ignored it: {row}")
                continue
            erp = {
                "nom": row["Enseigne"],
                "adresse": row["Adresse "],
                "code_postal": row["CP"],
                "commune": row["Ville"],
                "activite": activity,
                "sources": [{"source": ExternalSource.SOURCE_LAPOSTE, "source_id": row["N° Agrément"]}],
            }

            try:
                geo = geocode(erp["adresse"], erp["code_postal"])
            except RuntimeError:
                print("Cannot geolocate erp, ignoring it")
                continue
            if geo:
                for attr in ("numero", "voie", "lieu_dit", "code_postal", "commune", "code_insee"):
                    erp[attr] = geo[attr]
            else:
                print("Cannot geolocate erp, ignoring it")
                continue

            del erp["adresse"]

            handicaps = []
            accessibilite = dict()
            accessibilite["accueil_personnel"] = "personnel sensibilisé ou formé"
            accessibilite["commentaire"] = (
                "Auto-école adaptée à l’apprentissage de la conduite en situation handicap {handicap} (source : https://autoecoles.securite-routiere.gouv.fr/#/ )"
            )
            if row["Sourds ou malentendants"].lower() == "x":
                handicaps.append("auditif")

            if row["Handicap locomoteur"].lower() == "x":
                handicaps.append("locomoteur")
                accessibilite["entree_porte_presence"] = True
                accessibilite["entree_largeur_mini"] = 80
                accessibilite["entree_plain_pied"] = True
                accessibilite["accueil_cheminement_plain_pied"] = True
                accessibilite["accueil_retrecissement"] = False

            accessibilite["commentaire"] = accessibilite["commentaire"].format(handicap=" et ".join(handicaps))
            erp["accessibilite"] = accessibilite
            self._create_or_update_erp(data=erp)

    def _create_or_update_erp(self, data, erp=None):
        action = "created" if not erp else "updated"
        serializer = ErpImportSerializer(instance=erp, data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            if (
                isinstance(e, ValidationError)
                and "non_field_errors" in e.get_codes()
                and "duplicate" in e.get_codes()["non_field_errors"]
            ):
                existing_erp_pk = int(e.detail["non_field_errors"][1])
                existing_erp = Erp.objects.get(pk=existing_erp_pk)

                return self._create_or_update_erp(data=data, erp=existing_erp)

            return

        try:
            with reversion.create_revision():
                erp = serializer.save()
                reversion.set_comment("Created via auto_ecole import")
        except reversion.errors.RevertError:
            erp = serializer.save()
        except IntegrityError:
            print(f"Inconsistency in ERP accesibility {erp.nom}")

        print(f"ERP {erp.nom} {action}")
