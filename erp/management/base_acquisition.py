from django.core.management.base import BaseCommand


class BaseAcquisitionCommand(BaseCommand):
    def _is_enriching_access_data(self, initial_access_data, updated_access_data):
        if not initial_access_data:
            return True

        initial_data_dict = initial_access_data.__dict__
        updated_data_dict = updated_access_data.__dict__

        ignored_keys = {"id", "_state", "erp_id", "updated_at", "created_at", "completion_rate"}

        for key in updated_data_dict:
            if key in ignored_keys:
                continue

            initial_value = initial_data_dict.get(key)
            updated_value = updated_data_dict.get(key)

            if updated_value and initial_value is None:
                return True

        return False
