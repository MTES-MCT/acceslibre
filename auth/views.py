from django.contrib import messages
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django_registration.backends.activation.views import (
    RegistrationView,
    ActivationView,
)

from auth import forms
from auth.service import create_token, validate_from_token, send_activation_mail


class CustomActivationCompleteView(TemplateView):
    def get_context_data(self, **kwargs):
        "Spread the next redirect value from qs param to template context key."
        context = super().get_context_data(**kwargs)
        context["next"] = self.request.GET.get("next", "")
        return context


class CustomRegistrationView(RegistrationView):
    def get_email_context(self, activation_key):
        "Add the next redirect value to the email template context."
        context = super().get_email_context(activation_key)
        context["next"] = self.request.GET.get("next", "")
        return context


class CustomActivationView(ActivationView):
    def get_success_url(self, user=None):
        "Add the next redirect path to the success redirect url"
        url = super().get_success_url(user)
        next = self.request.GET.get("next", "")
        if not next and self.extra_context and "next" in self.extra_context:
            next = self.extra_context.get("next", "")
        return f"{url}?next={next}"


@login_required
def mon_compte(request):
    return render(request, "compte/index.html")


@login_required
def mon_identifiant(request):
    if request.method == "POST":
        form = forms.UsernameChangeForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            user = get_user_model().objects.get(id=request.user.id)
            old_username = user.username
            user.username = username
            user.save()
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(user).pk,
                object_id=user.id,
                object_repr=username,
                action_flag=CHANGE,
                change_message=f"Changement de nom d'utilisateur (avant: {old_username})",
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                f"Votre nom d'utilisateur a été changé en {user.username}.",
            )
            return redirect("mon_identifiant")
    else:
        form = forms.UsernameChangeForm(initial={"username": request.user.username})
    return render(
        request,
        "compte/mon_identifiant.html",
        context={"form": form},
    )


@login_required
def mon_email(request):
    if request.method == "POST":
        form = forms.EmailChangeForm(request.POST)
        if form.is_valid():
            new_email = form.cleaned_data["email1"]
            user = get_user_model().objects.get(id=request.user.id)

            token = create_token(user, new_email)
            send_activation_mail(token, new_email, user)

            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(user).pk,
                object_id=user.id,
                object_repr=new_email,
                action_flag=CHANGE,
                change_message=f"Demande de changement d'email {user.email} -> {new_email}",
            )
            messages.add_message(
                request,
                messages.INFO,
                f"Un email de validation vous a été envoyé à {user.email}. Merci de consulter votre boite de réception",
            )
            return redirect("mon_email")
    else:
        form = forms.EmailChangeForm(initial={"email": request.user.email})
    return render(
        request,
        "compte/mon_email.html",
        context={"form": form},
    )


@login_required
def change_email(request, activation_key):
    if not activation_key:
        return redirect("mon_email")

    user = get_user_model().objects.get(id=request.user.id)
    old_email = user.email

    failure = validate_from_token(user, activation_key)
    if failure:
        render(
            request,
            "compte/change_activation_failed.html",
            context={"activation_error": failure},
        )

    LogEntry.objects.log_action(
        user_id=request.user.id,
        content_type_id=ContentType.objects.get_for_model(user).pk,
        object_id=user.id,
        object_repr=user.email,
        action_flag=CHANGE,
        change_message=f"Email modifié {old_email} -> {user.email}",
    )

    messages.add_message(
        request,
        messages.SUCCESS,
        f"Votre email à été mis à jour avec succès !",
    )

    return redirect("mon_compte")

    # if request.user.id:
    #     return redirect("mon_compte")
    # else:
    #     render(
    #         request,
    #         "compte/change_activation_success.html",
    #         context={},
    #     )
