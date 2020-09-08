from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from erp.models import Erp
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
        queryset=get_user_model().objects, widget=forms.HiddenInput, required=False
    )
    erp = forms.ModelChoiceField(
        queryset=Erp.objects, widget=forms.HiddenInput, required=False
    )

    # form specific fields
    next = forms.CharField(required=False, widget=forms.HiddenInput)
    robot = forms.BooleanField(
        label="Je suis un robot",
        help_text="Merci de décocher cette case pour envoyer votre message",
        initial=True,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        initial = kwargs.get("initial", {})

        # prefill initial form data
        user = request.user
        if user.is_authenticated:
            initial["name"] = f"{user.first_name} {user.last_name}".strip()
            initial["email"] = user.email
            initial["user"] = user
        kwargs["initial"] = initial

        return super().__init__(*args, **kwargs)

    def clean_robot(self):
        robot = self.cleaned_data.get("robot", True)
        if robot is True:
            raise ValidationError(
                mark_safe("Décochez cette case pour soumettre le formulaire.")
            )
        return robot
