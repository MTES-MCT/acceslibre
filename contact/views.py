from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from core import mailer
from erp.models import Erp

from .forms import ContactForm
from .models import Message


def get_erp_contact_infos(erp):
    """Extracts ERP contact informations as a plain text list, for emails. This is mostly due to
    limitations of the Django templating system wrt whitespace formatting.
    """
    if not erp:
        return None
    infos = {
        "Adresse email": erp.contact_email,
        "Téléphone": erp.telephone,
        "Formulaire de contact": erp.contact_url,
        "Site internet": erp.site_internet,
    }
    return "\n".join(f"{k} : {v}" for (k, v) in infos.items() if v is not None)


def send_receipt(message):
    return mailer.send_email(
        [message.email],
        f"[{settings.SITE_NAME}] Suite à votre demande d'aide [{message.get_topic_display()}]",
        "mail/contact_form_receipt.txt",
        {
            "message_date": message.created_at,
            "user": message.user,
            "erp": message.erp,
            "contact_infos": get_erp_contact_infos(message.erp),
            "is_vaccination": message.topic == Message.TOPIC_VACCINATION
            or (
                message.erp
                and message.erp.metadata.get("centre_vaccination") is not None
            ),
            "SITE_NAME": settings.SITE_NAME,
            "SITE_ROOT_URL": settings.SITE_ROOT_URL,
        },
    )


def contact(request, topic=None, erp_slug=None):
    if topic and topic not in dict(Message.TOPICS):
        raise Http404("invalid subject")
    erp = Erp.objects.filter(slug=erp_slug).first() if erp_slug else None
    initial = {"topic": topic or Message.TOPIC_CONTACT, "erp": erp}
    if request.method == "POST":
        form = ContactForm(request.POST, request=request, initial=initial)
        if form.is_valid():
            message = form.save()
            subject = f"[{message.topic}] {message.get_topic_display()}"
            subject += f" ({erp.nom})" if erp else ""
            sent_ok = mailer.mail_admins(
                subject,
                "mail/contact_email.txt",
                {"message": message},
                reply_to=message.email,
            )
            message.sent_ok = sent_ok
            message.save()
            send_receipt(message)
            if erp:
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    "Votre message a été envoyé.",
                )
                return redirect(erp.get_absolute_url())
            else:
                return redirect(reverse("contact_form_sent"))
    else:
        form = ContactForm(request=request, initial=initial)
    return render(
        request,
        "contact_form/contact_form.html",
        context={"form": form, "erp": erp},
    )
