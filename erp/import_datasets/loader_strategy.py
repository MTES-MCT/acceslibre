from abc import ABC, abstractmethod

import requests


class Fetcher(ABC):
    @abstractmethod
    def fetch_data(cls, uri):
        pass


class JsonFetcher(Fetcher):
    def fetch_data(self, url):
        try:
            return requests.get(url).json()
        except requests.exceptions.RequestException as err:
            raise RuntimeError(
                f"Erreur de récupération des données JSON: {url}:\n  {err}"
            )


class FileFetcher(Fetcher):
    def fetch_data(self, filepath):
        ...
