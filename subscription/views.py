from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from erp.models import Erp
from subscription.models import ErpSubscription


@login_required
def subscribe_erp(request, erp_slug):
    erp = get_object_or_404(Erp.objects, slug=erp_slug)
    ErpSubscription.subscribe(erp, request.user)
    messages.add_message(
        request,
        messages.SUCCESS,
        "Vous êtes désormais abonné aux notifications de modification de cet établissement.",
    )
    return redirect(erp.get_absolute_url())


@login_required
def unsubscribe_erp(request, erp_slug):
    erp = get_object_or_404(Erp.objects, slug=erp_slug)
    ErpSubscription.unsubscribe(erp, request.user)
    messages.add_message(
        request,
        messages.SUCCESS,
        "Vous êtes désormais desabonné des notifications de modification de cet établissement.",
    )
    return redirect(erp.get_absolute_url())
