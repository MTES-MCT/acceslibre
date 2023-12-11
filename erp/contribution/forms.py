from django import forms

from erp.models import Accessibilite


class ContributionForm(forms.Form):
    class Meta:
        model = Accessibilite

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        question = kwargs.get("question")
        print(question)
        data = ""  # TODO
        choices = []  # TODO
        self.fields["question"] = forms.ChoiceField(label=data.label, required=True, choices=choices)
