from admin_two_factor.models import TwoFactorVerification
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver

from compte.models import UserPreferences, UserStats
from compte.tasks import sync_user_attributes
from erp.models import Accessibilite


@receiver(post_save, sender=get_user_model(), dispatch_uid="create_stats")
def save_user_create_stats(sender, instance, created, **kwargs):
    if created:
        user_stats = UserStats(user=instance)
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

    # FIXME: the editor is not necessarely the erp creator ! Wrong stats here
    user_stats, _ = UserStats.objects.get_or_create(user=instance.erp.user)
    user_stats.nb_erp_edited = F("nb_erp_edited") + 1
    user_stats.save(update_fields=("nb_erp_edited",))


@receiver(post_save, sender=get_user_model())
def save_profile(sender, instance, created, **kwargs):
    if created:
        user_prefs = UserPreferences(user=instance)
        user_prefs.save()

    if instance.is_superuser:
        # Create a 2FA object so that user can't access admin console without double authentification
        TwoFactorVerification.objects.get_or_create(user=instance, is_active=True)

    sync_user_attributes.delay(instance.pk)
