from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as translate_lazy
from reversion.models import Revision


class EmailToken(models.Model):
    class Meta:
        ordering = ("-created_at",)
        verbose_name = translate_lazy("EmailToken")
        verbose_name_plural = translate_lazy("EmailTokens")
        indexes = [
            models.Index(fields=["activation_token"]),
        ]

    activation_token = models.UUIDField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=translate_lazy("Utilisateur"),
        on_delete=models.CASCADE,
    )
    new_email = models.EmailField()
    expire_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class UserPreferences(models.Model):
    class Meta:
        verbose_name = translate_lazy("UserPreferences")
        verbose_name_plural = translate_lazy("UsersPreferences")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=translate_lazy("Utilisateur"),
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    notify_on_unpublished_erps = models.BooleanField(
        default=True,
        verbose_name=translate_lazy("Recevoir des mails de rappel de publication"),
    )
    newsletter_opt_in = models.BooleanField(
        default=False, verbose_name=translate_lazy("Accepte de recevoir la newsletter")
    )


class UserStats(models.Model):
    class Meta:
        verbose_name = translate_lazy("UserStats")
        verbose_name_plural = translate_lazy("UsersStats")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name=translate_lazy("Utilisateur"),
        on_delete=models.CASCADE,
        related_name="stats",
    )
    nb_erp_created = models.IntegerField(default=0)
    nb_erp_edited = models.IntegerField(default=0)
    nb_erp_attributed = models.IntegerField(default=0)
    nb_erp_administrator = models.IntegerField(default=0)
    nb_profanities = models.IntegerField(default=0)

    def __str__(self) -> str:
        return (
            f"for user #{self.user_id}: {self.nb_erp_created}/{self.nb_erp_edited}/{self.nb_erp_attributed}"
            f"/{self.nb_profanities}"
        )

    def get_date_last_contrib(self):
        last = Revision.objects.filter(user_id=self.user.pk).order_by("date_created").last()
        return last.date_created if last else None
