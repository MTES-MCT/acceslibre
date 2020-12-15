from django.conf import settings
from django.db import models

from subscription import managers


class ErpSubscription(models.Model):
    class Meta:
        unique_together = ("user", "erp")

    objects = managers.ErpSubscriptionQuerySet.as_manager()

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Utilisateur",
        on_delete=models.CASCADE,
    )
    erp = models.ForeignKey(
        "erp.Erp",
        verbose_name="Établissement",
        on_delete=models.CASCADE,
    )
    # datetimes
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Dernière modification"
    )

    @staticmethod
    def subscribe(erp, user):
        sub = ErpSubscription.objects.filter(user=user, erp=erp)
        if not sub:
            sub = ErpSubscription(user=user, erp=erp)
            sub.save()
        return sub

    @staticmethod
    def unsubscribe(erp, user):
        sub = ErpSubscription.objects.filter(user=user, erp=erp)
        if sub:
            sub.delete()
