import uuid
from datetime import datetime, timezone

from _datetime import timedelta
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import DatabaseError, models
from django.db.models import F
from django.urls import reverse

from compte.models import EmailToken, UserStats
from compte.tasks import sync_user_attributes
from core.lib import text
from core.mailer import BrevoMailer

DELETED_ACCOUNT_USERNAME = "anonyme"


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
    BrevoMailer().send_email(
        [email],
        template="email_change_activation",
        context={
            "username": user.username,
            "url_change_email": reverse("change_email", kwargs={"activation_token": activation_token}),
        },
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


def anonymize_user(user):
    user.email = ""
    user.username = f"{DELETED_ACCOUNT_USERNAME}{text.random_string(6)}"
    user.first_name = ""
    user.last_name = ""
    user.password = make_password(text.random_string(20))
    user.is_staff = False
    user.is_active = False
    user.is_superuser = False
    try:
        user.save()
        return user
    except (ValueError, DatabaseError) as err:
        raise RuntimeError(f"Erreur lors de la suppression du compte utilisateur: {err}")


def increment_nb_erp_created(user):
    if not user:
        return

    user_stats, _ = UserStats.objects.get_or_create(user=user)
    user_stats.nb_erp_created = F("nb_erp_created") + 1
    user_stats.save()
    sync_user_attributes.delay(user.pk)


def increment_nb_erp_edited(user):
    if not user:
        return

    user_stats, _ = UserStats.objects.get_or_create(user=user)
    user_stats.nb_erp_edited = F("nb_erp_edited") + 1
    user_stats.save()
