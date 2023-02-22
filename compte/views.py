import logging
from urllib.parse import unquote

from django.contrib import messages
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django_registration.backends.activation.views import ActivationView, RegistrationView

from compte import forms, service
from compte.models import UserPreferences
from erp import versioning
from erp.models import Erp
from subscription.models import ErpSubscription

logger = logging.getLogger(__name__)


class CustomRegistrationCompleteView(TemplateView):
    def get_context_data(self, **kwargs):
        "Spread the next redirect value from qs param to template context key."
        context = super().get_context_data(**kwargs)
        context["email"] = self.request.GET.get("email", "")
        context["next"] = self.request.GET.get("next", "")
        return context


class CustomActivationCompleteView(TemplateView):
    def get_context_data(self, **kwargs):
        "Spread the next redirect value from qs param to template context key."
        context = super().get_context_data(**kwargs)
        context["next"] = self.request.GET.get("next", "")
        return context


class CustomRegistrationView(RegistrationView):
    def get_success_url(self, user=None):
        return self.success_url + f"?email={user.email}&next={self.request.POST.get('next', '')}"

    def get_email_context(self, activation_key):
        "Add the next redirect value to the email template context."
        context = super().get_email_context(activation_key)
        context["next"] = self.request.POST.get("next", "")
        return context

    def get_context_data(self, **kwargs):
        "Add the next redirect value to the email template context."
        context = super().get_context_data(**kwargs)
        context["next"] = unquote(self.request.POST.get("next", self.request.GET.get("next", "")))
        return context


class CustomActivationView(ActivationView):
    def get_success_url(self, user=None):
        "Add the next redirect path to the success redirect url"
        url = super().get_success_url(user)
        #
        next = self.request.GET.get("next", "")
        if not next and self.extra_context and "next" in self.extra_context:
            next = self.extra_context.get("next", "")
        if next:
            login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
            return next
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
            user = request.user
            old_username = user.username
            user.username = username
            user.save()
            LogEntry.objects.log_action(
                user_id=user.id,
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
        form = forms.EmailChangeForm(request.POST, user=request.user)
        if form.is_valid():
            new_email = form.cleaned_data
            user = request.user

            activation_token = service.create_token(user, new_email)
            service.send_activation_mail(activation_token, new_email, user)

            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(user).pk,
                object_id=user.id,
                object_repr=new_email,
                action_flag=CHANGE,
                change_message=f"Demande de changement d'email {user.email} -> {new_email}",
            )
            return redirect("mon_email_sent")
    else:
        form = forms.EmailChangeForm(initial={"email": request.user.email})
    return render(
        request,
        "compte/mon_email.html",
        context={"form": form},
    )


def change_email(request, activation_token):
    if not activation_token:
        return redirect("mon_email")

    user, failure = service.validate_from_token(activation_token)
    if failure:
        render(
            request,
            "compte/email_change_activation_failed.html",
            context={"activation_error": failure},
        )

    LogEntry.objects.log_action(
        user_id=user.id,
        content_type_id=ContentType.objects.get_for_model(user).pk,
        object_id=user.id,
        object_repr=user.email,
        action_flag=CHANGE,
        change_message=f"Email modifié {user.email}",
    )

    messages.add_message(
        request,
        messages.SUCCESS,
        "Votre email à été mis à jour avec succès !",
    )

    if request.user.id:
        return redirect("mon_compte")
    else:
        return render(
            request,
            "compte/email_change_activation_success.html",
            context={},
        )


@login_required
def delete_account(request):
    if request.method == "POST":
        form = forms.AccountDeleteForm(request.POST)
        if form.is_valid():
            userid, old_username = request.user.id, request.user.username
            try:
                service.anonymize_user(request.user)
            except RuntimeError as err:
                logger.error(err)
                messages.add_message(
                    request,
                    messages.WARNING,
                    "Erreur lors de la désactivation du compte",
                )
                return redirect("mon_compte")
            logout(request)
            messages.add_message(request, messages.SUCCESS, "Votre compte à bien été supprimé")
            LogEntry.objects.log_action(
                user_id=userid,
                content_type_id=ContentType.objects.get_for_model(get_user_model()).pk,
                object_id=userid,
                object_repr=old_username,
                action_flag=CHANGE,
                change_message=f'Compte "{old_username}" désactivé et anonymisé',
            )
            return redirect("/")
    else:
        form = forms.AccountDeleteForm()
    return render(
        request,
        template_name="compte/delete_account_warning.html",
        context={"form": form},
    )


@login_required
def mes_erps(request):
    qs = Erp.objects.select_related("accessibilite", "activite", "commune_ext").filter(user_id=request.user.pk)
    if request.GET.get("q"):
        qs = qs.filter(nom__icontains=request.GET["q"])

    published_qs = qs.published()
    non_published_qs = qs.not_published()
    erp_total_count = qs.count()
    erp_published_count = published_qs.count()
    erp_non_published_count = non_published_qs.count()
    published = request.GET.get("published")
    if published == "1":
        qs = published_qs
    elif published == "0":
        qs = non_published_qs
    qs = qs.filter(user_id=request.user.pk).order_by("-updated_at")
    paginator = Paginator(qs, 10)
    pager = paginator.get_page(request.GET.get("page", 1))
    return render(
        request,
        "compte/mes_erps.html",
        context={
            "erp_total_count": erp_total_count,
            "erp_published_count": erp_published_count,
            "erp_non_published_count": erp_non_published_count,
            "pager": pager,
            "pager_base_url": f"?published={published or ''}",
            "filter_published": published,
            "q": request.GET.get("q") or "",
        },
    )


def _mes_contributions_view(request, qs, recues=False):
    paginator = Paginator(qs, 10)
    pager = paginator.get_page(request.GET.get("page", 1))
    return render(
        request,
        "compte/mes_contributions.html",
        context={"pager": pager, "recues": recues},
    )


@login_required
def mes_contributions(request):
    qs = versioning.get_user_contributions(request.user)
    return _mes_contributions_view(request, qs)


@login_required
def mes_contributions_recues(request):
    qs = versioning.get_user_contributions_recues(request.user)
    return _mes_contributions_view(request, qs, recues=True)


@login_required
def mes_abonnements(request):
    qs = (
        ErpSubscription.objects.select_related("erp", "erp__activite", "erp__commune_ext", "erp__user")
        .filter(user=request.user)
        .order_by("-updated_at")
    )
    paginator = Paginator(qs, 10)
    pager = paginator.get_page(request.GET.get("page", 1))
    return render(
        request,
        "compte/mes_abonnements.html",
        context={"pager": pager, "pager_base_url": "?1"},
    )


@login_required
def mes_challenges(request):
    qs = request.user.challenge_players.all().order_by("-inscriptions__inscription_date")
    paginator = Paginator(qs, 10)
    pager = paginator.get_page(request.GET.get("page", 1))
    return render(
        request,
        "compte/mes_challenges.html",
        context={"pager": pager, "pager_base_url": "?1"},
    )


@login_required
def mes_preferences(request):
    if request.method == "POST":
        form = forms.PreferencesForm(request.POST)
        if form.is_valid():
            prefs = UserPreferences.objects.get(user=request.user)
            prefs.notify_on_unpublished_erps = form.cleaned_data.get("notify_on_unpublished_erps")
            prefs.save()

            messages.add_message(request, messages.SUCCESS, "Vos préférences ont bien été enregistrées")

            return redirect("mes_preferences")
        pass
    else:
        form = forms.PreferencesForm(instance=request.user.preferences.get())
    return render(
        request,
        "compte/mes_preferences.html",
        context={"form": form},
    )
