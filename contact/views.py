from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import ContactForm


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST, request=request)
        if form.is_valid():
            # xxx: send mail
            # check mail errors
            # store model instance
            # create a task for resending unsent emails ?
            return redirect(reverse("contact_form_sent"))
    else:
        form = ContactForm(request=request)
    return render(request, "contact_form/contact_form.html", context={"form": form})
