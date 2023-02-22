from django.db.models.signals import post_save
from django.dispatch import receiver

from erp.models import Accessibilite
from erp.tasks import compute_access_completion_rate


@receiver(post_save, sender=Accessibilite)
def save_access(sender, instance, created, **kwargs):
    if "completion_rate" in (kwargs.get("update_fields") or []):
        # NOTE avoid infinite loop
        return

    compute_access_completion_rate.delay(instance.pk)
