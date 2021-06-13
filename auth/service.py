import uuid
from datetime import datetime, timezone

from _datetime import timedelta
from django.conf import settings
from django.db import models

from auth.models import EmailToken
from core import mailer

TEMPLATE_NAME = "auth/activation_changement_email_body.txt"


def create_token(user, email, activation_token=None, today=datetime.now(timezone.utc)):
    activation_key = activation_token or uuid.uuid4()
    email_token = EmailToken(
        activation_token=activation_key,
        user=user,
        new_email=email,
        expire_at=today + timedelta(days=settings.EMAIL_ACTIVATION_DAYS),
    )
    email_token.save()

    return activation_key


def send_activation_mail(activation_key, email, user):
    context = {
        "activation_key": activation_key,
        "user": user,
        "SITE_NAME": settings.SITE_NAME,
        "SITE_ROOT_URL": settings.SITE_ROOT_URL,
    }

    mailer.send_email(
        [email],
        f"Activation de votre compte {settings.SITE_NAME.title}",
        TEMPLATE_NAME,
        context,
    )


def validate_from_token(user, activation_key, today=datetime.now(timezone.utc)):
    try:
        email_token = EmailToken.objects.get(token=activation_key)
    except models.ObjectDoesNotExist:
        return "Token invalide"

    if (email_token.user is None) or (email_token.user != user):
        return "Utilisateur non trouvé"

    if email_token.expire_at < today:
        return "Token expiré"

    user.email = email_token.new_email
    user.save()

    email_token.delete()

    return None
