from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from .models import Message


class ContactForm(forms.ModelForm):
    class Meta:
        model = Message
        exclude = (
            "created_at",
            "updated_at",
            "sent_ok",
        )

    # hide relations
    user = forms.ModelChoiceField(
        queryset=get_user_model().objects, widget=forms.HiddenInput
    )
    erp = forms.IntegerField(required=False, widget=forms.HiddenInput)

    # form specific fields
    next = forms.CharField(required=False, widget=forms.HiddenInput)
    robot = forms.BooleanField(
        label="Je suis un robot",
        help_text="Afin de lutter contre le spam, assurez-vous de décocher cette case pour envoyer votre message",
        initial=True,
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        initial = kwargs.get("initial", {})

        # retrieve user information
        user = request.user
        if user.is_authenticated:
            initial["name"] = f"{user.first_name} {user.last_name}".strip()
            initial["email"] = user.email
            initial["user"] = user

        # retrieve erp information
        erp = kwargs.pop("erp")
        if erp:
            initial["body"] = f"Mon message concerne cet établissement : {erp.nom}\n\n"

        # prefill initial form data
        kwargs["initial"] = initial
        return super().__init__(*args, **kwargs)

    def clean_robot(self):
        robot = self.cleaned_data.get("robot", True)
        if robot is True:
            raise ValidationError(
                mark_safe("Décochez cette case pour soumettre le formulaire.")
            )
        return robot
