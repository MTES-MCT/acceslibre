from django.shortcuts import get_object_or_404, reverse
from django.views.generic.edit import FormView

import erp.contribution.conditions as condition_module
from erp.contribution import CONTRIBUTION_QUESTIONS
from erp.models import Erp

from .forms import ContributionForm

# Working url : http://127.0.0.1:8000/contrib/v2/step/mairie-42/0


class ContributionStepView(FormView):
    template_name = "contrib/includes/contribution-step.html"

    def dispatch(self, request, *args, **kwargs):
        self.erp = get_object_or_404(Erp, slug=kwargs.get("erp_slug"))
        self.step = kwargs.get("step_number")
        return super().dispatch(request, *args, **kwargs)

    def _get_question(self):
        # TODO error handling if step does not exists
        return CONTRIBUTION_QUESTIONS[self.step]

    def get_form(self, form_class=None):
        # TODO should we chec0 for conditions here ?
        question = self._get_question()
        return ContributionForm(question=question, **self.get_form_kwargs())

    def _get_next_question_number(self):
        # TODO handle cases with display conditions

        next_question_number = self.step + 1

        while True:
            # TODO handle end of process / error
            next_question = CONTRIBUTION_QUESTIONS[next_question_number]

            if not next_question.display_conditions:
                return next_question_number

            should_display = []
            for condition_name in next_question.display_conditions:
                condition = getattr(condition_module, condition_name)
                result = condition(access=self.erp.accessibilite)
                should_display.append(result)

            should_display_question = all(should_display)
            if should_display_question:
                return next_question_number

            next_question_number += 1

    def get_success_url(self):
        return reverse(
            "contribution-step", kwargs={"erp_slug": self.erp.slug, "step_number": self._get_next_question_number()}
        )

    def form_valid(self, form):
        # TODO move me to form.save() ?
        question = self._get_question()
        access = self.erp.accessibilite

        # TODO simplify this ?
        for answer in question.answers:
            if answer.label == form.cleaned_data.get("question"):
                for modelisation in answer.modelisations:
                    setattr(access, modelisation["field"], modelisation["value"])

        access.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        # TODO handle errors
        print("IN FORM INVALID")
        print(form.non_field_errors())
        for field in form:
            print(field.errors)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["erp"] = self.erp
        return context
