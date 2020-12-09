from django.conf import settings
from django.db import models

from erp.models import Commune, Erp


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Utilisateur",
        on_delete=models.CASCADE,
    )
    commune = models.ForeignKey(
        Commune,
        verbose_name="Commune",
        on_delete=models.CASCADE,
    )
    content_object = models.GenericForeignKey("content_type", "object_id")

    @staticmethod
    def subscribe(commune, user):
        sub = Subscription.objects.filter(user=user, commune=commune)
        if not sub:
            sub = Subscription(user=user, commune=commune)
            sub.save()
        return sub

    @staticmethod
    def unsubscribe(commune, user):
        sub = Subscription.objects.filter(user=user, commune=commune)
        if not sub:
            return
        return sub.delete()
