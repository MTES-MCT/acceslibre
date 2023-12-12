from django import forms

from erp.models import Accessibilite

from .exceptions import UnknownQuestionTypeException


class ContributionForm(forms.Form):
    class Meta:
        model = Accessibilite

    def __init__(self, *args, **kwargs):
        self.question = kwargs.pop("question")
        super().__init__(*args, **kwargs)

        if self.question.is_unique_type or self.question.is_unique_or_int_type:
            self.fields["question"] = forms.ChoiceField(
                label=self.question.label,
                required=True,
                choices=self.question.choices,
                widget=forms.RadioSelect,
            )
        # elif self.question.is_unique_or_int_type:
        #     assert False
        else:
            raise UnknownQuestionTypeException

    def save(self, accessibility):
        # TODO simplify this ?
        for answer in self.question.answers:
            if answer.label == self.cleaned_data.get("question"):
                for modelisation in answer.modelisations:
                    setattr(accessibility, modelisation["field"], modelisation["value"])

        accessibility.save()
