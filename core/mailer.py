from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def mail_admins(subject, template, context=None, reply_to=None):
    context = context if context else {}
    context["SITE_NAME"] = settings.SITE_NAME
    context["SITE_ROOT_URL"] = settings.SITE_ROOT_URL

    email = EmailMessage(
        subject=subject,
        body=render_to_string(template, context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.DEFAULT_FROM_EMAIL],
        reply_to=[reply_to] if reply_to else [settings.DEFAULT_FROM_EMAIL],
    )
    # Note: The return value will be the number of successfully delivered messages
    # (which can be 0 or 1 since send_mail can only send one message).
    return 1 == email.send(fail_silently=True)
