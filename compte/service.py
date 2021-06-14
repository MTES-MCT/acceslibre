import uuid
from datetime import datetime, timezone

from _datetime import timedelta
from django.conf import settings
from django.db import models

from compte.models import EmailToken
from core import mailer

TEMPLATE_NAME = "compte/email_change_activation_email.txt"


def create_token(user, email, activation_token=None, today=datetime.now(timezone.utc)):
    activation_token = activation_token or uuid.uuid4()
    email_token = EmailToken(
        activation_token=activation_token,
        user=user,
        new_email=email,
        expire_at=today + timedelta(days=settings.EMAIL_ACTIVATION_DAYS),
    )
    email_token.save()

    return activation_token


def send_activation_mail(activation_token, email, user):
    context = {
        "activation_token": activation_token,
        "user": user,
        "SITE_NAME": settings.SITE_NAME,
        "SITE_ROOT_URL": settings.SITE_ROOT_URL,
    }

    mailer.send_email(
        [email],
        f"Activation de votre compte {settings.SITE_NAME.title()}",
        TEMPLATE_NAME,
        context,
    )


def validate_from_token(activation_token, today=datetime.now(timezone.utc)):
    try:
        email_token = EmailToken.objects.get(activation_token=activation_token)
        user = email_token.user
    except models.ObjectDoesNotExist:
        return None, "Token invalide"

    if user is None:
        return None, "Utilisateur non trouvé"

    if email_token.expire_at < today:
        return user, "Token expiré"

    user.email = email_token.new_email
    user.save()

    email_token.delete()

    return user, None
