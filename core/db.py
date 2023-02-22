from django.conf import settings
from django.db.migrations import Migration


class MigrationIgnoredInTest(Migration):
    """
    To be used only with migrations which do not alter schema, only running python scripts managing data.
    """

    def apply(self, project_state, schema_editor, collect_sql=False):
        if not settings.TEST:
            return super().apply(project_state, schema_editor, collect_sql)
        return project_state
