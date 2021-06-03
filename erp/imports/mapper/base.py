import abc
from typing import Dict

from erp.models import Erp, Activite


class BaseRecordMapper(abc.ABC):
    @property
    @abc.abstractmethod
    def dataset_url(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def activite(self) -> str:
        pass

    @abc.abstractmethod
    def fetch_data(self) -> Dict[str, str]:
        pass

    @abc.abstractmethod
    def process(self, record: Dict[str, str], activite: Activite) -> Erp:
        pass
