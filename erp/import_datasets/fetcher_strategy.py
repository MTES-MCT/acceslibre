import csv
import io
from abc import ABC, abstractmethod
from typing import Any, List, Iterable

import requests


class Fetcher(ABC):
    fieldnames: List

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
    def __init__(self, delimiter=",", fieldnames=None):
        self.delimiter = delimiter
        self.fieldnames = fieldnames

    def fetch(self, url) -> Iterable[Any]:
        try:
            csvfile = requests.get(url).content.decode("utf8")
        except requests.exceptions.RequestException as err:
            raise RuntimeError(
                f"Erreur de récupération des données JSON: {url}:\n  {err}"
            )

        try:
            return csv.DictReader(
                io.StringIO(csvfile),
                delimiter=self.delimiter,
                fieldnames=self.fieldnames,
            )
        except csv.Error as err:
            raise RuntimeError(f"Erreur de lecture des données CSV: {url}:\n  {err}")


class VoidFetcher(Fetcher):
    def fetch(self, anything):
        return None


class StringFetcher(Fetcher):
    def __init__(self, content):
        self.content = content

    def fetch(self, data=None):
        return self.content
