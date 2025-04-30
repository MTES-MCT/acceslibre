import logging
from urllib.parse import unquote

from django.contrib import messages
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordResetView
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django_registration.backends.activation.views import ActivationView, RegistrationView

from compte import forms, service
from compte.forms import CustomAuthenticationForm, CustomPasswordResetForm
from compte.models import UserPreferences
from compte.tasks import sync_user_attributes
from core.mailer import BrevoMailer
from erp import versioning
from erp.models import Erp
from stats.models import ChallengePlayer
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

    def get_context_data(self, **kwargs):
        "Add the next redirect value to the email template context."
        context = super().get_context_data(**kwargs)
        context["next"] = unquote(self.request.POST.get("next", self.request.GET.get("next", "")))
        return context

    def send_activation_email(self, user):
        activation_key = self.get_activation_key(user)
        context = {}
        context["activation_key"] = activation_key
        context["username"] = user.username
        context["next"] = unquote(self.request.POST.get("next", self.request.GET.get("next", ""))) or "/"
        return BrevoMailer().send_email(to_list=user.email, template="account_activation", context=context)

    def create_inactive_user(self, form):
        """
        Create the inactive user account and send an email containing
        activation instructions.

        """
        new_user = form.save(commit=False)
        new_user.is_active = False
        new_user.save()

        preferences = new_user.preferences.get()
        preferences.newsletter_opt_in = form.cleaned_data["newsletter_opt_in"]
        preferences.save()

        self.send_activation_email(new_user)

        return new_user


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


def manage_change_username_form(form, request):
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


def manage_change_email_form(form, request):
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


@login_required
def my_profile(request):
    preferences = UserPreferences.objects.get(user=request.user)
    form_label = request.POST.get("form_label")

    form_login = None
    form_email = None
    form_preferences = None
    form_password_change = None
    form_delete_account = None

    if request.method == "POST":
        if form_label == "password-change":
            form_password_change = forms.PasswordChangeForm(request.user, request.POST)
            if form_password_change.is_valid():
                form_password_change.save()
                messages.add_message(request, messages.SUCCESS, "Votre mot de passe a bien été modifié.")
                return redirect("my_profile")

        if form_label == "username-change":
            form_login = forms.UsernameChangeForm(request.POST)

            if form_login.is_valid():
                manage_change_username_form(form_login, request)
                return redirect("my_profile")

        if form_label == "email-change":
            form_email = forms.EmailChangeForm(request.POST, user=request.user)

            if form_email.is_valid():
                manage_change_email_form(form_email, request)
                return redirect("mon_email_sent")

        if form_label == "delete-account":
            form_delete_account = forms.AccountDeleteForm(request.POST)
            if form_delete_account.is_valid():
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
                    return redirect("my_profile")
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

        if form_label == "preferences":
            form_preferences = forms.PreferencesForm(request.POST, instance=preferences)

            if form_preferences.is_valid():
                form_preferences.save()
                messages.add_message(request, messages.SUCCESS, "Vos préférences ont bien été enregistrées")
                sync_user_attributes.delay(request.user.pk)
                return redirect("my_profile")

    form_login = form_login or forms.UsernameChangeForm(initial={"username": request.user.username})
    form_email = form_email or forms.EmailChangeForm(initial={"email": request.user.email})
    form_preferences = form_preferences or forms.PreferencesForm(instance=preferences)
    form_password_change = form_password_change or forms.PasswordChangeForm(request.user)
    form_delete_account = form_delete_account or forms.AccountDeleteForm()

    return render(
        request,
        "compte/my_profile.html",
        context={
            "form_login": form_login,
            "form_email": form_email,
            "form_preferences": form_preferences,
            "form_password_change": form_password_change,
            "form_delete_account": form_delete_account,
            "page_type": "my-profile",
            "submitted_form": form_label,
            "bread_crumb_url": "test",
        },
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
        return redirect("my_profile")
    else:
        return render(
            request,
            "compte/email_change_activation_success.html",
            context={},
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


@login_required
def mes_contributions(request):
    qs = versioning.get_user_contributions(request.user)
    nb_contributions_received = versioning.get_user_contributions_recues(request.user).count()
    paginator = Paginator(qs, 10)
    pager = paginator.get_page(request.GET.get("page", 1))
    return render(
        request,
        "compte/mes_contributions.html",
        context={
            "pager": pager,
            "contributions_received_tab_active": False,
            "contributions_done_tab_active": True,
            "nb_contributions_received": nb_contributions_received,
            "nb_contributions_done": qs.count(),
        },
    )


@login_required
def mes_contributions_recues(request):
    qs = versioning.get_user_contributions_recues(request.user)
    nb_contributions_done = versioning.get_user_contributions(request.user).count()
    paginator = Paginator(qs, 10)
    pager = paginator.get_page(request.GET.get("page", 1))
    return render(
        request,
        "compte/mes_contributions.html",
        context={
            "pager": pager,
            "contributions_received_tab_active": True,
            "contributions_done_tab_active": False,
            "nb_contributions_received": qs.count(),
            "nb_contributions_done": nb_contributions_done,
        },
    )


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
    qs = ChallengePlayer.objects.filter(player=request.user).order_by("-inscription_date")
    paginator = Paginator(qs, 10)
    pager = paginator.get_page(request.GET.get("page", 1))
    return render(
        request,
        "compte/mes_challenges.html",
        context={"pager": pager, "pager_base_url": "?1"},
    )


def set_api_key(request):
    if request.method == "POST":
        request.session["api_key"] = request.POST["api_key"]
    return redirect("apidocs")


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm


class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_type"] = "login-form"
        return context
