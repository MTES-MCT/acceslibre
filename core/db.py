from django.conf import settings
from django.db.migrations import Migration
from django.db.migrations.operations.base import Operation


class MigrationIgnoredInTest(Migration):
    """
    To be used only with migrations which do not alter schema, only running python scripts managing data.
    """

    def apply(self, project_state, schema_editor, collect_sql=False):
        if not settings.TEST:
            return super().apply(project_state, schema_editor, collect_sql)
        return project_state


class OperationIgnoredInTest(Operation):
    reduces_to_sql = False
    reversible = False

    def __init__(self, *args, **kwargs):
        pass

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        pass

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        pass

    def describe(self):
        return "Operation ignored in test"

    @property
    def migration_name_fragment(self):
        return "operation_ignore_in_test"
