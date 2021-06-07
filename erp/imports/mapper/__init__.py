class SkippedRecord(Exception):
    pass


class UnpublishedRecord(Exception):
    def __init__(self, *args, erp=None, **kwargs):
        self.erp = erp
        super().__init__(*args, **kwargs)
