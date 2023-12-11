from django import forms

from erp.models import Accessibilite


class ContributionForm(forms.Form):
    class Meta:
        model = Accessibilite

    def __init__(self, *args, **kwargs):
        question = kwargs.pop("question")
        super().__init__(*args, **kwargs)
        self.fields["question"] = forms.ChoiceField(label=question.label, required=True, choices=question.choices, widget=forms.RadioSelect)
