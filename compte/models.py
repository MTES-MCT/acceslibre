from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


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

    @receiver(post_save, sender=User)
    def save_profile(sender, instance, created, **kwargs):
        if created:
            user_prefs = UserPreferences(user=instance)
            user_prefs.save()
