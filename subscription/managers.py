from django.db import models


class ErpSubscriptionQuerySet(models.QuerySet):
    def subscribed_by_user(self, user):
        return self.filter(user=user)

    def subscribers(self, erp):
        return self.filter(erp=erp)
