from django.apps import AppConfig


class StatsConfig(AppConfig):
    name = "stats"

    def ready(self):
        from stats import signals  # noqa
