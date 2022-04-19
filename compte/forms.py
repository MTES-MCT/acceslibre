from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.safestring import mark_safe
from django_registration.forms import RegistrationFormUniqueEmail

from compte.models import UserPreferences

USERNAME_RULES = "Uniquement des lettres, nombres et les caractères « . », « - » et « _ » (les espaces sont interdits)"


def validate_username_whitelisted(value):
    if value.lower() in settings.USERNAME_BLACKLIST:
        raise ValidationError(
            "Ce nom d'utilisateur est réservé", params={"value": value}
        )


def define_username_field():
    return forms.CharField(
        max_length=32,
        required=False,
        label="Nom d’utilisateur",
        validators=[
            RegexValidator(r"^[\w.-]+\Z", message=USERNAME_RULES),
            validate_username_whitelisted,
        ],
    )


def define_email_field(label="Email"):
    return forms.EmailField(
        required=True,
        label=label,
        widget=forms.TextInput(attrs={"placeholder": "Exemple: nom@domaine.com"}),
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
        ]

    email = forms.EmailField(
        error_messages={
            "invalid": "Format de l'email attendu : nom@domaine.tld",
            "unique": "Cet email est déja utilisé. Merci de fournir un email différent.",
        }
    )

    username = define_username_field()
    next = forms.CharField(required=False)

    robot = forms.BooleanField(
        label="Je ne suis pas un robot",
        initial=False,
        required=False,
    )

    def clean_robot(self):
        robot = self.cleaned_data["robot"]
        if not robot:
            raise ValidationError(
                "Vous devez cocher cette case pour soumettre le formulaire"
            )
        return robot


class UsernameChangeForm(forms.Form):
    username = define_username_field()

    def clean_username(self):
        username = self.cleaned_data["username"]
        if get_user_model().objects.filter(username__iexact=username).count() > 0:
            raise ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username


class EmailChangeForm(forms.Form):
    email1 = define_email_field("Nouvelle adresse email")
    email2 = define_email_field("Confirmation de la nouvelle adresse email")

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        email1 = self.cleaned_data.get("email1")
        email2 = self.cleaned_data.get("email2")

        if self.user and email1 == self.user.email:
            raise ValidationError("Vous n'avez pas modifié votre adresse email")

        if email1 != email2:
            raise ValidationError("Les emails ne correspondent pas")

        if get_user_model().objects.filter(email__iexact=email1).count() > 0:
            raise ValidationError(
                "Cette adresse email existe déjà, "
                "veuillez choisir une adresse email différente"
            )

        return email1


class AccountDeleteForm(forms.Form):
    confirm = forms.BooleanField(
        label="Confirmer la suppression de mon compte utilisateur. J'ai bien compris que cette opération est irréversible.",
        required=True,
    )

    def clean_confirm(self):
        confirm = self.cleaned_data["confirm"]
        if confirm is not True:
            raise ValidationError(
                "Vous devez confirmer la suppression pour la rendre effective."
            )
        return confirm


class PreferencesForm(forms.ModelForm):
    class Meta:
        model = UserPreferences
        fields = ["notify_on_unpublished_erps"]
