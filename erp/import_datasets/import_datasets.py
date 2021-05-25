import logging

from django.db import DataError

from erp.import_datasets.base_mapper import BaseRecordMapper
from erp.import_datasets.print_strategy import outputPrintStrategy, outputVoidStrategy
from erp.models import Activite, Accessibilite

logger = logging.getLogger(__name__)


class ImportDatasets:
    output = None
    errors = []
    imported = 0
    skipped = 0

    def __init__(self, mapper: BaseRecordMapper, is_scheduler=False) -> None:
        self.output = outputVoidStrategy if is_scheduler else outputPrintStrategy
        assert mapper.dataset_url is not None
        self.mapper = mapper

    def job(self, verbose=False):
        # reinitialize class instance properties, as it's long-lived
        # accross imports in a scheduler context
        self.imported = 0
        self.skipped = 0
        self.errors = []

        try:
            for erp in self.do_import():
                self.output("." if erp else "S", "", True)
        except RuntimeError as err:
            logger.error(err)

        if verbose and len(self.errors) > 0:
            self.output("Erreurs rencontrées :")
            for error in self.errors:
                self.output(f"- {error}")

        self.output("Opération effectuée:")
        self.output(f"- {self.imported} ERP(s) importé(s)")
        self.output(f"- {self.skipped} écarté(s)")

        return self.imported, self.skipped, self.errors

    def do_import(self):
        try:
            data = self.mapper.fetch_data()
        except RuntimeError as err:
            raise RuntimeError("Error fetching data: ", str(err))

        return self._process_data(data)

    def _process_data(self, records):
        activite = Activite.objects.filter(slug=self.mapper.activite).first()
        if not activite:
            raise RuntimeError(f"L'activité {activite} n'existe pas.")

        for record in records:
            try:
                erp = self.mapper.process(record, activite)
                self._save_erp(erp)
                self.imported += 1
                yield erp
            except RuntimeError as err:
                self.errors.append(f"{err.__str__()}")
                self.skipped += 1
                yield None

    def _save_erp(self, erp):
        try:
            # Save erp instance
            erp.published = True
            erp.save()

            # Attach an Accessibilite to newly created Erps
            if not erp.has_accessibilite():
                accessibilite = Accessibilite(erp=erp)
                accessibilite.save()
        except DataError as err:
            raise RuntimeError(f"Erreur à l'enregistrement des données: {err}") from err
