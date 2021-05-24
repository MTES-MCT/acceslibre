import abc

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
    def fetch_data(self):
        pass

    @abc.abstractmethod
    def process(self, records, activite: Activite) -> Erp:
        pass
