from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from erp.models import Erp

from .forms import ContactForm
from .models import Message


def contact(request, subject=None, erp_slug=None):
    if subject and subject not in dict(Message.TOPICS):
        raise Http404("invalid subject")
    erp = Erp.objects.filter(slug=erp_slug).first() if erp_slug else None
    if request.method == "POST":
        form = ContactForm(request.POST, request=request, erp=erp)
        if form.is_valid():
            # message = form.save()
            # send mail
            # message.sent_ok = <result of sending>
            # message.save()
            # bonus: create a task for resending unsent emails ?
            return redirect(reverse("contact_form_sent"))
    else:
        form = ContactForm(request=request, erp=erp)
    return render(request, "contact_form/contact_form.html", context={"form": form})
