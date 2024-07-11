import logging

from django.conf import settings
from sib_api_v3_sdk import (
    AddContactToList,
    ApiClient,
    Configuration,
    ContactsApi,
    CreateAttribute,
    CreateContact,
    SendSmtpEmail,
    SendSmtpEmailReplyTo,
    SendSmtpEmailSender,
    SendSmtpEmailTo,
    TransactionalEmailsApi,
    UpdateContact,
)
from sib_api_v3_sdk.rest import ApiException
from waffle import switch_is_active

from compte.serializers import ErpSerializerForBrevo, UserStatsForBrevoSerializer
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task()
def send_async_email(to_list, template, context):
    BrevoMailer().send_email(to_list=to_list, template=template, context=context)


class Mailer:
    def send_email(self, to_list, template, context=None, reply_to=None):
        raise NotImplementedError

    def mail_admins(self, *args, **kwargs):
        return self.send_email([settings.DEFAULT_EMAIL], *args, **kwargs)


class BrevoMailer(Mailer):
    configuration = None

    def __init__(self) -> None:
        self.configuration = Configuration()
        self.configuration.api_key["api-key"] = settings.BREVO_API_KEY
        super().__init__()

    def send_email(self, to_list, template, context=None, reply_to=None):
        if not to_list:
            return False

        if not isinstance(to_list, (list, set, tuple)):
            to_list = [to_list]

        context = context or {}
        context["site_name"] = settings.SITE_NAME
        context["site_url"] = settings.SITE_ROOT_URL

        if template not in settings.BREVO_TEMPLATE_IDS:
            logger.error(f"Template {template} not found")
            return False

        template_id = settings.BREVO_TEMPLATE_IDS.get(template)
        send_smtp_email = SendSmtpEmail(
            to=[SendSmtpEmailTo(email=to) for to in to_list],
            sender=SendSmtpEmailSender(email=settings.DEFAULT_EMAIL),
            template_id=template_id,
            params=context,
            reply_to=SendSmtpEmailReplyTo(email=reply_to) if reply_to else None,
        )
        api_instance = TransactionalEmailsApi(ApiClient(self.configuration))

        if not switch_is_active("USE_REAL_EMAILS"):
            return True

        try:
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

        if "DATE_LAST_CONTRIB" not in current_attributes:
            api_instance.create_attribute(
                attribute_name="DATE_LAST_CONTRIB",
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
                create_attribute=CreateAttribute(type="text"),
            )

        if "NB_ERPS" not in current_attributes:
            api_instance.create_attribute(
                attribute_name="NB_ERPS",
                attribute_category="normal",
                create_attribute=CreateAttribute(type="float"),
            )

        if "AVERAGE_COMPLETION_RATE" not in current_attributes:
            api_instance.create_attribute(
                attribute_name="AVERAGE_COMPLETION_RATE",
                attribute_category="normal",
                create_attribute=CreateAttribute(type="float"),
            )

        if "ERP_URL" not in current_attributes:
            api_instance.create_attribute(
                attribute_name="ERP_URL",
                attribute_category="normal",
                create_attribute=CreateAttribute(type="text"),
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

        if not hasattr(user, "stats"):
            return False

        serializer = UserStatsForBrevoSerializer(instance=user.stats)
        update_contact = UpdateContact(attributes=serializer.data)
        api_instance.update_contact(contact.id, update_contact)
        return True

    def sync_erp(self, erp):
        if not erp.import_email:
            return False

        api_instance = ContactsApi(ApiClient(self.configuration))
        try:
            contact = api_instance.get_contact_info(erp.import_email)
        except ApiException:
            return False

        serializer = ErpSerializerForBrevo(instance=erp)
        update_contact = UpdateContact(attributes=serializer.data)
        api_instance.update_contact(contact.id, update_contact)
        return True

    def add_to_list(self, list_name, email):
        if not list_name or not email:
            return False

        if not (list_id := settings.BREVO_CONTACT_LIST_IDS.get(list_name)):
            return False

        api_instance = ContactsApi(ApiClient(self.configuration))
        contact_emails = AddContactToList(emails=[email])

        try:
            api_instance.add_contact_to_list(list_id, contact_emails)
            return True
        except ApiException:
            return False
