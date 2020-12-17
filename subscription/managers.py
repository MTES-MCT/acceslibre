from django.db import models


class ErpSubscriptionQuerySet(models.QuerySet):
    def subscribed_by_user(self, user):
        return self.filter(user=user, erp__is_published=True)

    def subscribers(self, erp):
        return self.filter(erp=erp, user__is_active=True)
