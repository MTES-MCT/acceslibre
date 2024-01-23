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
        elif self.question.is_mutiple_type:
            self.fields["question"] = forms.MultipleChoiceField(
                label=self.question.label,
                required=False,
                choices=self.question.choices,
                widget=forms.CheckboxSelectMultiple,
            )
        elif self.question.is_free_text_type:
            self.fields["question"] = forms.CharField(label=self.question.label, max_length=1000, required=False)
        else:
            raise UnknownQuestionTypeException

    def _apply_choice_answer(self, users_answer, accessibility):
        picked_answer = next(a for a in self.question.answers if a.label == users_answer)
        for modelisation in picked_answer.modelisations:
            setattr(accessibility, modelisation["field"], modelisation["value"])

    def save(self, accessibility):
        if self.question.is_unique_type:
            self._apply_choice_answer(self.cleaned_data.get("question"), accessibility)
        elif self.question.is_mutiple_type:
            for users_answer in self.cleaned_data.get("question"):
                self._apply_choice_answer(users_answer, accessibility)
        elif self.question.is_unique_or_int_type:
            field = self.question.answers[0].modelisations[0]["field"]
            users_answer = self.cleaned_data.get("question")
            setattr(accessibility, field, users_answer if users_answer else None)
        elif self.question.is_free_text_type:
            users_answer = self.cleaned_data.get("question")
            setattr(accessibility, self.question.free_text_field, users_answer if users_answer else None)
        else:
            raise UnknownQuestionTypeException

        accessibility.save()
