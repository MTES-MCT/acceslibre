from django import forms

from .exceptions import UnknownQuestionTypeException


class ContributionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.question = kwargs.pop("question")
        super().__init__(*args, **kwargs)

        if self.question.is_unique_type:
            self.fields["question"] = forms.ChoiceField(
                label=self.question.label,
                required=True,
                choices=self.question.choices,
                widget=forms.RadioSelect,
            )
        elif self.question.is_unique_or_int_type:
            self.fields["question"] = forms.IntegerField(label=self.question.label, required=False)
            self.fields["question"].widget.input_type = "int_or_radio"
            self.fields["question"].widget.unique_label = self.question.answers[0].label
        else:
            raise UnknownQuestionTypeException

    def save(self, accessibility):
        users_answer = self.cleaned_data.get("question")
        if self.question.is_unique_type:
            picked_answer = next(a for a in self.question.answers if a.label == users_answer)
            for modelisation in picked_answer.modelisations:
                setattr(accessibility, modelisation["field"], modelisation["value"])
        elif self.question.is_unique_or_int_type:
            field = self.question.answers[0].modelisations[0]["field"]
            setattr(accessibility, field, users_answer if users_answer else None)
        else:
            raise UnknownQuestionTypeException

        accessibility.save()
