from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth.password_validation import password_validators_help_texts
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.urls import reverse
from django.utils.functional import lazy
from django.utils.html import format_html
from django.utils.translation import gettext as translate
from django.utils.translation import gettext_lazy as translate_lazy
from django_registration import validators
from django_registration.forms import RegistrationFormUniqueEmail
from six import text_type

from compte.models import UserPreferences
from core.mailer import BrevoMailer

USERNAME_RULES = translate(
    "Uniquement des lettres, nombres et les caractères « . », « - » et « _ » (les espaces sont interdits)"
)


def validate_username_whitelisted(value):
    if value.lower() in settings.USERNAME_BLACKLIST:
        raise ValidationError(translate_lazy("Ce nom d'utilisateur est réservé"), params={"value": value})


def define_username_field():
    return forms.CharField(
        max_length=32,
        required=True,
        label="",
        validators=[
            RegexValidator(r"^[\w.-]+\Z", message=USERNAME_RULES),
            validate_username_whitelisted,
        ],
        widget=forms.TextInput(
            attrs={"class": "fr-input", "autocomplete": "username", "aria-describedby": "username-desc-error"},
        ),
    )


def define_email_field():
    return forms.EmailField(
        required=True,
        label="",
        widget=forms.TextInput(
            attrs={"class": "fr-input", "autocomplete": "on", "aria-describedby": "email-error-desc"}
        ),
    )


def _custom_password_validators_help_text_html(password_validators=None):
    """
    Return an HTML string with all help texts of all configured validators
    in an <ul>.
    """
    help_texts = password_validators_help_texts(password_validators)
    help_items = [format_html("<span>* {}</span><br>", help_text) for help_text in help_texts]
    # <------------- append your hint here in help_items  ------------->
    return "%s" % "".join(help_items) if help_items else ""


custom_password_validators_help_text_html = custom_validators_help_text_html = lazy(
    _custom_password_validators_help_text_html, text_type
)


class CustomRegistrationForm(RegistrationFormUniqueEmail):
    class Meta(RegistrationFormUniqueEmail.Meta):
        model = get_user_model()
        fields = [
            "username",
            "email",
            "password1",
            "password2",
            "next",
            "newsletter_opt_in",
        ]

    email = forms.EmailField(
        error_messages={
            "invalid": translate_lazy("Format de l'email attendu : nom@domaine.tld"),
            "unique": translate_lazy("Cet email est déja utilisé. Merci de fournir un email différent."),
        },
    )
    password1 = forms.CharField(
        label=translate_lazy("Password"),
        required=True,
        widget=forms.PasswordInput,
        strip=False,
        help_text=custom_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=translate_lazy("Confirmation du mot de passe"),
        required=True,
        widget=forms.PasswordInput,
        strip=False,
    )
    username = define_username_field()
    next = forms.CharField(required=False)

    robot = forms.BooleanField(
        label=translate_lazy("Je ne suis pas un robot*"),
        initial=False,
        required=True,
    )

    newsletter_opt_in = forms.BooleanField(
        initial=False,
        required=False,
        label=translate_lazy("J'accepte de recevoir la newsletter"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        email_field = get_user_model().get_email_field_name()
        self.fields[email_field].validators = (
            validators.CaseInsensitiveUnique(get_user_model(), email_field, validators.DUPLICATE_EMAIL),
        )
        self.fields["email"].widget = forms.TextInput(
            attrs={
                "autocomplete": "email",
                "class": "fr-input",
                "autofocus": True,
                "required": True,
                "type": "email",
                "aria-describedby": "email-desc-error",
            }
        )
        self.fields["username"].widget = forms.TextInput(
            attrs={
                "autocomplete": "username",
                "class": "fr-input",
                "required": True,
                "aria-describedby": "username-desc-error",
            }
        )
        self.fields["password1"].widget = forms.TextInput(
            attrs={
                "class": "fr-input fr-password__input",
                "type": "password",
                "required": True,
                "aria-describedby": "password1-desc-error",
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].widget = forms.TextInput(
            attrs={
                "class": "fr-input fr-password__input",
                "type": "password",
                "required": True,
                "aria-describedby": "password2-desc-error",
                "autocomplete": "new-password",
            }
        )

    def clean_robot(self):
        robot = self.cleaned_data["robot"]
        if not robot:
            raise ValidationError(translate_lazy("Vous devez cocher cette case pour soumettre le formulaire"))
        return robot


class PasswordChangeForm(DjangoPasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs.update(
            {
                "class": "fr-password__input fr-input",
                "aria-describedby": "password-1-input-messages",
                "aria-required": True,
                "autocomplete": "current-password",
            }
        )
        self.fields["new_password1"].widget.attrs.update(
            {
                "class": "fr-password__input fr-input",
                "aria-describedby": "password-2-input-messages",
                "aria-required": True,
                "autocomplete": "new-password",
            }
        )
        self.fields["new_password2"].widget.attrs.update(
            {
                "class": "fr-password__input fr-input",
                "aria-describedby": "password-3-input-messages",
                "aria-required": True,
                "autocomplete": "new-password",
            }
        )

    form_label = forms.CharField(widget=forms.HiddenInput(), initial="password-change")


class UsernameChangeForm(forms.Form):
    form_label = forms.CharField(widget=forms.HiddenInput(), initial="username-change")
    username = define_username_field()

    def clean_username(self):
        username = self.cleaned_data["username"]
        if get_user_model().objects.filter(username__iexact=username).count():
            raise ValidationError(translate_lazy("Ce nom d'utilisateur est déjà pris."))
        return username


class EmailChangeForm(forms.Form):
    form_label = forms.CharField(widget=forms.HiddenInput(), initial="email-change")
    email1 = define_email_field()
    email2 = define_email_field()

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        email1 = self.cleaned_data.get("email1")
        email2 = self.cleaned_data.get("email2")

        if self.user and email1 == self.user.email:
            raise ValidationError(translate_lazy("Vous n'avez pas modifié votre adresse email"))

        if email1 != email2:
            raise ValidationError(translate_lazy("Les emails ne correspondent pas"))

        if get_user_model().objects.filter(email__iexact=email1).count():
            raise ValidationError(
                translate_lazy("Cette adresse email existe déjà, veuillez choisir une adresse email différente")
            )

        return email1


class AccountDeleteForm(forms.Form):
    confirm = forms.BooleanField(
        label=translate_lazy(
            "Confirmer la suppression de mon compte utilisateur. J'ai bien compris que cette opération est irréversible."
        ),
        required=True,
    )

    def clean_confirm(self):
        confirm = self.cleaned_data["confirm"]
        if confirm is not True:
            raise ValidationError(translate_lazy("Vous devez confirmer la suppression pour la rendre effective."))
        return confirm


class PreferencesForm(forms.ModelForm):
    form_label = forms.CharField(widget=forms.HiddenInput(), initial="preferences")

    class Meta:
        model = UserPreferences
        fields = ["notify_on_unpublished_erps", "newsletter_opt_in"]


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget = forms.EmailInput(attrs={"class": "fr-input", "autocomplete": "username"})
        self.fields["password"].widget.attrs.update(
            {"class": "fr-password__input fr-input", "autocomplete": "current-password"}
        )


class CustomPasswordResetForm(PasswordResetForm):
    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        BrevoMailer().send_email(
            to_list=to_email,
            template="password_reset",
            context={
                "username": context["user"].username,
                "url_password_reset": reverse(
                    "password_reset_confirm", kwargs={"uidb64": context["uid"], "token": context["token"]}
                ),
            },
        )
