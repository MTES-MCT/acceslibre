from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django_registration.forms import RegistrationFormUniqueEmail

USERNAME_RULES = "Uniquement des lettres, nombres et les caractères « . », « - » et « _ » (les espaces sont interdits)"


def validate_username_whitelisted(value):
    if value.lower() in settings.USERNAME_BLACKLIST:
        raise ValidationError(
            "Ce nom d'utilisateur est réservé", params={"value": value}
        )


def define_username_field():
    return forms.CharField(
        max_length=32,
        help_text=f"Requis. 32 caractères maximum. {USERNAME_RULES}. "
        "Note : ce nom d'utilisateur pourra être affiché publiquement sur le site si vous contribuez.",
        required=True,
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
    )


class CustomRegistrationForm(RegistrationFormUniqueEmail):
    class Meta(RegistrationFormUniqueEmail.Meta):
        model = get_user_model()
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
            "next",
            "robot",
        ]

    username = define_username_field()
    next = forms.CharField(required=False)
    robot = forms.BooleanField(
        label="Je suis un robot",
        help_text="Merci de décocher cette case avant de soumettre le formulaire",
        initial=True,
        required=False,
    )

    def clean_robot(self):
        robot = self.cleaned_data["robot"]
        if robot:
            raise ValidationError(
                "Vous devez décocher cette case pour soumettre le formulaire"
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
    email1 = define_email_field("Nouvel email")
    email2 = define_email_field("Confirmation nouvel email")

    def clean(self):
        super().clean()
        email1 = self.cleaned_data.get("email1")
        email2 = self.cleaned_data.get("email2")

        if email1 != email2:
            raise ValidationError("Les emails ne correspondent pas")

        if get_user_model().objects.filter(email__iexact=email1).count() > 0:
            raise ValidationError("Veuillez choisir un email différent")
        return email1
