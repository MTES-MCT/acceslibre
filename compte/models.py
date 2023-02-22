from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from compte.tasks import sync_user_attributes


class EmailToken(models.Model):
    class Meta:
        ordering = ("-created_at",)
        verbose_name = "EmailToken"
        verbose_name_plural = "EmailTokens"
        indexes = [
            models.Index(fields=["activation_token"]),
        ]

    activation_token = models.UUIDField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Utilisateur",
        on_delete=models.CASCADE,
    )
    new_email = models.EmailField()
    expire_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class UserPreferences(models.Model):
    class Meta:
        verbose_name = "UserPreferences"
        verbose_name_plural = "UsersPreferences"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Utilisateur",
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    notify_on_unpublished_erps = models.BooleanField(
        default=True,
        verbose_name="Recevoir des mails de rappel de publication",
    )

    @receiver(post_save, sender=get_user_model())
    def save_profile(sender, instance, created, **kwargs):
        if created:
            user_prefs = UserPreferences(user=instance)
            user_prefs.save()

        sync_user_attributes.delay(instance.pk)


class UserStats(models.Model):
    class Meta:
        verbose_name = "UserStats"
        verbose_name_plural = "UsersStats"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="Utilisateur",
        on_delete=models.CASCADE,
        related_name="stats",
    )
    nb_erp_created = models.IntegerField(default=0)
    nb_erp_edited = models.IntegerField(default=0)
    nb_erp_attributed = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"for user #{self.user_id}: {self.nb_erp_created}/{self.nb_erp_edited}/{self.nb_erp_attributed}"
