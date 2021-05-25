import csv
from abc import ABC, abstractmethod
from typing import Any, List, Iterable

import requests


class Fetcher(ABC):
    @abstractmethod
    def fetch(self, uri) -> Any:
        pass


class JsonFetcher(Fetcher):
    def fetch(self, url):
        try:
            return requests.get(url).json()
        except requests.exceptions.RequestException as err:
            raise RuntimeError(
                f"Erreur de récupération des données JSON: {url}:\n  {err}"
            )


class CsvFetcher(Fetcher):
    def fetch(self, url) -> Iterable[Any]:
        try:
            csvfile = requests.get(url).text
        except requests.exceptions.RequestException as err:
            raise RuntimeError(
                f"Erreur de récupération des données JSON: {url}:\n  {err}"
            )

        try:
            return csv.reader(csvfile)
        except csv.Error as err:
            raise RuntimeError(f"Erreur de lecture des données CSV: {url}:\n  {err}")


class FileFetcher(Fetcher):
    def fetch(self, filepath):
        ...
