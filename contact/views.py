from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from core import mailer
from erp.models import Erp

from .forms import ContactForm
from .models import Message


def contact(request, topic=None, erp_slug=None):
    if topic and topic not in dict(Message.TOPICS):
        raise Http404("invalid subject")
    erp = Erp.objects.filter(slug=erp_slug).first() if erp_slug else None
    initial = initial = {"topic": topic, "erp": erp}
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
            return redirect(reverse("contact_form_sent"))
    else:
        form = ContactForm(request=request, initial=initial)
    return render(
        request, "contact_form/contact_form.html", context={"form": form, "erp": erp}
    )
