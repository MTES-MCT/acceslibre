from celery import shared_task
from django.contrib.auth.models import User

from core.mailer import BrevoMailer


@shared_task()
def sync_user_attributes(user_pk):
    user = User.objects.get(pk=user_pk)
    BrevoMailer().sync_user(user)
