from django import forms


class ContactForm(forms.Form):
    subject = forms.CharField(label="Sujet", required=True)
    name = forms.CharField(label="Votre nom", required=False)
    email = forms.EmailField(label="Adresse email", required=True)
    body = forms.CharField(label="Message", required=True, widget=forms.Textarea)
    next = forms.CharField(required=False, widget=forms.HiddenInput)
    username = forms.CharField(required=False, widget=forms.HiddenInput)
    erp_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    verif = forms.BooleanField(label="Je ne suis pas un spammeur", required=True)

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        initial = kwargs.get("initial", {})

        # retrieve user information
        user = request.user
        if user.is_authenticated:
            initial["name"] = f"{user.first_name} {user.last_name}".strip()
            initial["email"] = user.email
            initial["username"] = user.username

        # retrieve erp information
        erp_id = kwargs.get("erp_id")
        if erp_id:
            initial["erp_id"] = erp_id

        # prefill initial form data
        kwargs["initial"] = initial
        return super().__init__(*args, **kwargs)
