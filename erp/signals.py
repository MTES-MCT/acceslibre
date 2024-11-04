from django.db.models.signals import post_save
from django.dispatch import receiver

from erp.models import Accessibilite, ActivitySuggestion, Erp, ExternalSource
from erp.tasks import check_for_activity_suggestion_spam, compute_access_completion_rate


@receiver(post_save, sender=Accessibilite)
def save_access(sender, instance, created, **kwargs):
    if "completion_rate" in (kwargs.get("update_fields") or []):
        # NOTE avoid infinite loop
        return

    compute_access_completion_rate.delay(instance.pk)


@receiver(post_save, sender=ActivitySuggestion)
def save_activity_suggestion(sender, instance, created, **kwargs):
    if not created or not instance.user:
        return

    check_for_activity_suggestion_spam.delay(instance.pk)


@receiver(post_save, sender=Erp)
def sync_source(sender, instance, created, **kwargs):
    if not instance.source or not instance.source_id:
        return

    ExternalSource.objects.filter(source=instance.source, erp_id=instance.id).delete()
    ExternalSource.objects.create(erp_id=instance.id, source=instance.source, source_id=instance.source_id)
