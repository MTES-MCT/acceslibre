from django.apps import AppConfig


class ErpConfig(AppConfig):
    name = "erp"

    def ready(self):
        from erp import signals  # noqa
