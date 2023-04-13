import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django_registration.backends.activation.views import RegistrationView
from sib_api_v3_sdk import (
    ApiClient,
    Configuration,
    ContactsApi,
    CreateAttribute,
    CreateContact,
    SendSmtpEmail,
    SendSmtpEmailSender,
    SendSmtpEmailTo,
    TransactionalEmailsApi,
    UpdateContact,
)
from sib_api_v3_sdk.rest import ApiException
from waffle import switch_is_active

logger = logging.getLogger(__name__)


class Mailer:
    # FIXME: when all mails will be migrated, clean those args, should be sufficient to keep only to_list, template and context
    def send_email(self, to_list, subject, template, context=None, reply_to=None, fail_silently=True):
        raise NotImplementedError

    def mail_admins(self, *args, **kwargs):
        return self.send_email([settings.DEFAULT_EMAIL], *args, **kwargs)


class DefaultMailer(Mailer):
    def send_email(self, to_list, subject, template, context=None, reply_to=None, fail_silently=True):
        context = context if context else {}
        context["SITE_NAME"] = settings.SITE_NAME
        context["SITE_ROOT_URL"] = settings.SITE_ROOT_URL

        email = EmailMessage(
            subject=subject,
            body=render_to_string(template, context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to_list,
            reply_to=[reply_to] if reply_to else [settings.DEFAULT_FROM_EMAIL],
        )
        # Note: The return value will be the number of successfully delivered messages
        # (which can be 0 or 1 since send_mail can only send one message).
        return 1 == email.send(fail_silently=fail_silently)


class SendInBlueMailer(Mailer):
    configuration = None

    def __init__(self) -> None:
        self.configuration = Configuration()
        self.configuration.api_key["api-key"] = settings.SEND_IN_BLUE_API_KEY
        super().__init__()

    def send_email(self, to_list, subject, template, context=None, reply_to=None, fail_silently=True):
        if not to_list:
            return False

        if not isinstance(to_list, (list, set, tuple)):
            to_list = [to_list]

        context = context or {}
        context["site_name"] = settings.SITE_NAME
        context["site_url"] = settings.SITE_ROOT_URL

        if template not in settings.SEND_IN_BLUE_TEMPLATE_IDS:
            logger.error(f"Template {template} not found")
            return False

        template_id = settings.SEND_IN_BLUE_TEMPLATE_IDS.get(template)
        send_smtp_email = SendSmtpEmail(
            to=[SendSmtpEmailTo(email=to) for to in to_list],
            sender=SendSmtpEmailSender(email=settings.DEFAULT_EMAIL),
            template_id=template_id,
            params=context,
        )
        api_instance = TransactionalEmailsApi(ApiClient(self.configuration))

        try:
            if switch_is_active("USE_REAL_EMAILS"):
                api_instance.send_transac_email(send_smtp_email)
            return True
        except ApiException:
            return False

    def create_default_user_attributes(self):
        # FIXME: unused in code, but has to be launched before being able to sync_user
        api_instance = ContactsApi(ApiClient(self.configuration))
        current_attributes = [a.to_dict()["name"] for a in api_instance.get_attributes().attributes]

        if "DATE_JOINED" not in current_attributes:
            api_instance.create_attribute(
                attribute_name="DATE_JOINED",
                attribute_category="normal",
                create_attribute=CreateAttribute(type="date"),
            )

        if "IS_ACTIVE" not in current_attributes:
            api_instance.create_attribute(
                attribute_name="IS_ACTIVE",
                attribute_category="normal",
                create_attribute=CreateAttribute(type="boolean"),
            )

        if "ACTIVATION_KEY" not in current_attributes:
            api_instance.create_attribute(
                attribute_name="ACTIVATION_KEY",
                attribute_category="normal",
                create_attribute=CreateAttribute(type="str"),
            )

    def sync_user(self, user):
        if not user.email:
            return False

        api_instance = ContactsApi(ApiClient(self.configuration))
        try:
            contact = api_instance.get_contact_info(user.email)
        except ApiException as exc:
            if exc.reason == "Not Found":
                contact = api_instance.create_contact(CreateContact(email=user.email))
            else:
                return False

        update_contact = UpdateContact(
            attributes={
                "DATE_JOINED": user.date_joined.strftime("%Y-%m-%d"),
                "IS_ACTIVE": user.is_active,
                "NOM": user.last_name,
                "PRENOM": user.first_name,
                "ACTIVATION_KEY": RegistrationView().get_activation_key(user) if not user.is_active else "",
            }
        )
        api_instance.update_contact(contact.id, update_contact)
        return True


def get_mailer():
    return DefaultMailer()
