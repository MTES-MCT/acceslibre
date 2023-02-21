from django.apps import AppConfig


class CompteConfig(AppConfig):
    name = "compte"

    def ready(self):
        from compte import signals  # noqa
