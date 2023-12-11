from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404, redirect, render
from erp.contribution import CONTRIBUTION_QUESTIONS
from .forms import ContributionForm
from erp.models import Erp

# Working url : http://127.0.0.1:8000/contrib/v2/step/mairie-42/0

class ContributionStepView(FormView):
    template_name = "contrib/includes/contribution-step.html"

    def dispatch(self, request, *args, **kwargs):
        self.erp = get_object_or_404(Erp, slug=kwargs.get("erp_slug"))
        self.step = kwargs.get("step_number")
        return super().dispatch(request, *args, **kwargs)

    def _get_question_list(self):
        return CONTRIBUTION_QUESTIONS
    def get_form(self, form_class=None):
        questions = self._get_question_list()

        # TODO error handling
        question = questions[self.step]
        should_display_question = True
        for display_condition in question.display_conditions:
            assert False
            pass # TODO find a way to execute condition


        if not should_display_question:
            assert False # TODO

        return ContributionForm(question=question)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["erp"] = self.erp
        return context

# TODO handle post ?

