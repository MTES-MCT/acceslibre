from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver

from compte.models import UserStats
from compte.tasks import sync_user_attributes
from erp.models import Accessibilite, Erp


@receiver(post_save, sender=get_user_model(), dispatch_uid="create_stats")
def save_user_create_stats(sender, instance, created, **kwargs):
    if created:
        user_stats = UserStats(user=instance)
        user_stats.save()


@receiver(post_save, sender=Erp, dispatch_uid="update_stats_from_erp")
def save_erp_update_stats(sender, instance, created, **kwargs):
    if not instance.user:
        return

    user_stats, _ = UserStats.objects.get_or_create(user=instance.user)
    if created:
        user_stats.nb_erp_created = F("nb_erp_created") + 1
        sync_user_attributes.delay(instance.user.pk)
    else:
        user_stats.nb_erp_edited = F("nb_erp_edited") + 1

    user_stats.save()


@receiver(post_save, sender=UserStats, dispatch_uid="check_for_blacklisting")
def check_for_user_blacklisting(sender, instance, **kwargs):
    if "nb_profanities" not in (kwargs.get("update_fields") or []):
        return

    # As user_stats attributes can be instances of CombinedExpression (because we use F objects) and not resolved
    # as an int in Django post save signals for perf reasons, we refresh it from db.
    instance.refresh_from_db()
    if instance.nb_profanities > settings.NB_PROFANITIES_IGNORED:
        instance.user.is_active = False
        instance.user.save()


@receiver(post_save, sender=Accessibilite, dispatch_uid="update_stats_from_accessibility")
def save_access_update_stats(sender, instance, created, **kwargs):
    if not instance.erp.user_id:
        return

    if created:
        # considering that nb_erp_edited will be incremented with erp creation and not accessibility one.
        return

    if "completion_rate" in (kwargs.get("update_fields") or []):
        # ignore internal changes made on completion_rate
        return

    user_stats, _ = UserStats.objects.get_or_create(user=instance.erp.user)
    user_stats.nb_erp_edited = F("nb_erp_edited") + 1
    user_stats.save(update_fields=("nb_erp_edited",))


erp_claimed = Signal()


@receiver(erp_claimed, dispatch_uid="update_stats_after_erp_claimed")
def erp_claimed_update_stats(sender, instance, **kwargs):
    if not instance.user:
        # This case should never happen, as user is here to self assign the ERP
        return

    user_stats, _ = UserStats.objects.get_or_create(user=instance.user)
    user_stats.nb_erp_attributed = F("nb_erp_attributed") + 1
    user_stats.save(update_fields=("nb_erp_attributed",))
