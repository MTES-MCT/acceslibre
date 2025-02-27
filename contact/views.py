from itertools import groupby

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from core.mailer import BrevoMailer
from erp.models import Erp

from .forms import ContactForm
from .models import FAQ, Message


def send_receipt(message):
    context = {
        "message_date": message.created_at.strftime("%Y-%m-%d à %H:%M"),
        "erp": message.erp.nom if message.erp else "",
    }
    if message.erp:
        context["contact_infos"] = {
            "contact_email": message.erp.contact_email,
            "telephone": message.erp.telephone,
            "contact_url": message.erp.contact_url,
            "site_internet": message.erp.site_internet,
        }
    return BrevoMailer().send_email(
        [message.email],
        context=context,
        template="contact_receipt",
    )


def contact(request, topic=Message.TOPIC_CONTACT, erp_slug=None):
    topic = topic if topic in dict(Message.TOPICS) else Message.TOPIC_CONTACT
    erp = Erp.objects.filter(slug=erp_slug).first() if erp_slug else None
    initial = {"topic": topic or Message.TOPIC_CONTACT, "erp": erp}
    if request.method == "POST":
        form = ContactForm(request.POST, request=request, initial=initial)
        if form.is_valid():
            message = form.save()
            context = {
                "message": {
                    "name": message.name,
                    "body": message.body,
                    "username": message.user.username if message.user else None,
                    "topic": message.get_topic_display(),
                    "email": message.email,
                },
            }
            if erp:
                context["message"]["erp"] = {
                    "nom": erp.nom,
                    "adresse": erp.adresse,
                    "absolute_url": erp.get_absolute_url(),
                }
            sent_ok = BrevoMailer().mail_admins(
                context=context,
                reply_to=message.email,
                template="contact_to_admins",
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
            return redirect(reverse("contact_form_sent"))
    else:
        form = ContactForm(request=request, initial=initial)
    return render(
        request,
        "contact/contact_form.html",
        context={"form": form, "erp": erp, "page_type": "contact-form"},
    )


def faq(request):
    faqs = FAQ.objects.all().order_by("section")

    faq_by_section = {
        section_name: list(items)
        for section, section_name in FAQ.SECTION_CHOICES
        for key, items in groupby(faqs, lambda x: x.section)
        if key == section
    }

    context = {
        "faq_by_section": faq_by_section,
    }
    return render(request, "contact/faq.html", context)
