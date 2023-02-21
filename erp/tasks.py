from celery import shared_task

from erp.models import Accessibilite
from erp.schema import FIELDS


@shared_task()
def compute_access_completion_rate(accessibilite_pk):
    try:
        access = Accessibilite.objects.get(pk=accessibilite_pk)
    except Accessibilite.DoesNotExist:
        return

    root_fields = [field for field in FIELDS if FIELDS[field].get("root") is True]
    nb_fields = len(root_fields)

    nb_filled_in_fields = 0
    for attr in root_fields:
        # NOTE: we can not use bool() here, as False is a filled in info
        if getattr(access, attr) not in (None, [], ""):
            nb_filled_in_fields += 1

    access.completion_rate = nb_filled_in_fields * 100 / nb_fields
    access.save(update_fields=["completion_rate"])
