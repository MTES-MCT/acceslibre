from django.contrib.auth.models import User
from django.db import models


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
        User,
        verbose_name="Utilisateur",
        on_delete=models.CASCADE,
    )
    new_email = models.EmailField()
    expire_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
