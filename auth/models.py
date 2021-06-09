import datetime

from django.contrib.auth.models import User
from django.db import models


class EmailChangeAuth(models.Model):
    auth_key = models.UUIDField()
    user = models.ForeignKey(
        User,
        verbose_name="Utilisateur",
        on_delete=models.CASCADE,
    )
    new_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
