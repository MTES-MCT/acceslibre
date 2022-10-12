import csv
import io
import json
import tarfile

import ijson
import requests


class Fetcher:
    def fetch(self, url):
        try:
            return requests.get(url)
        except requests.exceptions.RequestException as err:
            raise RuntimeError(f"Erreur de lecture des données JSON\n  {err}")


class JsonFetcher(Fetcher):
    def __init__(self, hook=lambda x: x):
        self.hook = hook

    def fetch(self, url):
        try:
            res = super().fetch(url).json()
            return self.hook(res)
        except KeyError as err:
            raise RuntimeError(f"Erreur de clé JSON: {err}")
        except json.JSONDecodeError as err:
            raise RuntimeError(f"Erreur de décodage des données JSON:\n  {err}")
        except requests.exceptions.RequestException as err:
            raise RuntimeError(f"Erreur de récupération des données JSON:\n  {err}")


class JsonCompressedFetcher(Fetcher):
    def __init__(self, hook=lambda x: x):
        self.hook = hook

    def fetch(self, url):
        try:
            print(f"Récupération des données sur {url}")
            res = super().fetch(url)
            open("sp.bz2", "wb").write(res.content)
            print("Récupération des données => [OK]")
            with tarfile.open("sp.bz2", "r:bz2") as tar:
                for tarinfo in tar:
                    if tarinfo.isreg() and "-data.gouv_local.json" in tarinfo.name:
                        print(f"Extraction des données sur le fichier {tarinfo}")
                        f = tar.extractfile(tarinfo)
                        print("Extraction des données => [OK]")
                        for item in ijson.items(f, "service.item"):
                            yield item
        except KeyError as err:
            raise RuntimeError(f"Erreur de clé JSON: {err}")
        except json.JSONDecodeError as err:
            raise RuntimeError(f"Erreur de décodage des données JSON:\n  {err}")
        except requests.exceptions.RequestException as err:
            raise RuntimeError(f"Erreur de récupération des données JSON:\n  {err}")


class CsvFetcher(Fetcher):
    def __init__(self, delimiter=",", fieldnames=None):
        self.delimiter = delimiter
        self.fieldnames = fieldnames

    def fetch(self, url):
        try:
            csv_contents = super().fetch(url).content.decode("utf8")
            return csv.DictReader(
                io.StringIO(csv_contents),
                delimiter=self.delimiter,
                fieldnames=self.fieldnames,
            )
        except csv.Error as err:
            raise RuntimeError(f"Erreur de lecture des données CSV:\n  {err}")
        except requests.exceptions.RequestException as err:
            raise RuntimeError(
                f"Erreur de récupération des données CSV: {url}:\n  {err}"
            )


class CsvFileFetcher(CsvFetcher):
    def fetch(self, url):
        try:
            csv_contents = open(url, "r", encoding="utf-8-sig").read()
            return csv.DictReader(
                io.StringIO(csv_contents),
                delimiter=self.delimiter,
                fieldnames=self.fieldnames,
            )
        except csv.Error as err:
            raise RuntimeError(f"Erreur de lecture des données CSV:\n  {err}")
