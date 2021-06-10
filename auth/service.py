import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from auth.models import EmailChange


TEMPLATE_NAME = "django_registration/activation_changement_email_body.txt"


def create_and_send_token(user, email):
    """
    Send the activation email. The activation key is the username,
    signed using TimestampSigner.

    """
    activation_key = uuid.uuid4()
    print(activation_key)
    email_changer = EmailChange(auth_key=activation_key, user=user, new_email=email)
    email_changer.save()
    print(email_changer.auth_key)

    context = {
        "activation_key": activation_key,
        "user": user,
        "SITE_NAME": settings.SITE_NAME,
        "SITE_ROOT_URL": settings.SITE_ROOT_URL,
    }

    print(context.get("activation_user"))

    message = render_to_string(
        template_name=TEMPLATE_NAME,
        context=context,
    )
    print(message)
    user.email_user(
        f"Activation de votre compte {settings.SITE_NAME.title}",
        message,
        settings.DEFAULT_FROM_EMAIL,
    )
