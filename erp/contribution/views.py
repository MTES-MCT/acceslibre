from django.http import Http404
from django.shortcuts import get_object_or_404, render, reverse
from django.views.generic.edit import FormView

from erp.contribution import CONTRIBUTION_QUESTIONS, get_next_question_number, get_previous_question_number
from erp.models import Erp

from .exceptions import ContributionStopIteration
from .forms import ContributionForm


class ContributionStepView(FormView):
    template_name = "contrib/contribution-step.html"

    def dispatch(self, request, *args, **kwargs):
        self.erp = get_object_or_404(Erp, slug=kwargs.get("erp_slug"))
        self.step = kwargs.get("step_number")
        return super().dispatch(request, *args, **kwargs)

    def _get_question(self):
        try:
            return CONTRIBUTION_QUESTIONS[self.step]
        except IndexError:
            raise Http404

    def get_form(self, form_class=None):
        question = self._get_question()
        return ContributionForm(question=question, **self.get_form_kwargs())

    def get_success_url(self):
        try:
            next_question = get_next_question_number(self.step, erp=self.erp)
            return reverse("contribution-step", kwargs={"erp_slug": self.erp.slug, "step_number": next_question})
        except ContributionStopIteration:
            return reverse("contribution-base-success", kwargs={"erp_slug": self.erp.slug})

    def form_valid(self, form):
        form.save(self.erp.accessibilite)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["erp"] = self.erp
        context["step"] = self.step + 1
        context["nb_step"] = len(CONTRIBUTION_QUESTIONS) + 1
        try:
            question_number = get_previous_question_number(self.step, erp=self.erp)
            url = reverse("contribution-step", kwargs={"erp_slug": self.erp.slug, "step_number": question_number})
            context["previous_url"] = url
        except ContributionStopIteration:
            pass
        return context


def contribution_base_success_view(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug)
    return render(
        request,
        "contrib/contribution-base-success.html",
        context={"erp": erp},
    )
