from django.db import models


class ErpSubscriptionQuerySet(models.QuerySet):
    def subscribers(self, erp):
        return self.filter(erp=erp, user__is_active=True)
