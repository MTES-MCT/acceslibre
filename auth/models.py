from django.contrib.auth.models import User
from django.db import models


class EmailChange(models.Model):
    class Meta:
        ordering = ("created_at",)
        verbose_name = "EmailChange"
        verbose_name_plural = "EmailChanges"
        indexes = [
            models.Index(fields=["token"]),
        ]

    token = models.UUIDField()
    user = models.ForeignKey(
        User,
        verbose_name="Utilisateur",
        on_delete=models.CASCADE,
    )
    new_email = models.EmailField()
    expire_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
