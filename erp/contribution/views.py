from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, render, reverse
from django.utils.translation import gettext as translate
from django.views.generic.edit import FormView

from erp.contribution import (
    ADDITIONAL_CONTRIBUTION_QUESTIONS,
    CONTRIBUTION_QUESTIONS,
    get_next_question_number,
    get_previous_question_number,
)
from erp.models import Accessibilite, Erp
from erp.contribution.access_utils import UNSURE_ANSWER

from .exceptions import ContributionStopIteration
from .forms import ContributionForm


class ContributionStepMixin(FormView):
    question_set = None
    route_name = None
    success_route_name = None

    def dispatch(self, request, *args, **kwargs):
        self.erp = get_object_or_404(Erp, slug=kwargs.get("erp_slug"))
        self.step = kwargs.get("step_number")
        return super().dispatch(request, *args, **kwargs)

    def _get_question(self):
        try:
            return self.question_set[self.step]
        except IndexError:
            raise Http404

    def get_form(self, form_class=None):
        question = self._get_question()
        return ContributionForm(question=question, **self.get_form_kwargs())

    def form_valid(self, form):
        form.save(self.erp.accessibilite)
        return super().form_valid(form)

    def _has_minimum_of_answers(self):
        if self.erp.published:
            return True

        fields_to_exclude = ["id", "erp", "conformite", "registre_url", "completion_rate", "created_at", "updated_at"]
        fields_to_check = [f.name for f in Accessibilite._meta.get_fields() if f.name not in fields_to_exclude]
        access = self.erp.accessibilite
        fields_values = [getattr(access, f) for f in fields_to_check if getattr(access, f) not in (None, [], "")]
        return len(fields_values) >= settings.MIN_NB_ANSWERS_IN_CONTRIB_V2

    def get_success_url(self):
        try:
            next_question = get_next_question_number(self.step, erp=self.erp, questions=self.question_set)
            return reverse(self.route_name, kwargs={"erp_slug": self.erp.slug, "step_number": next_question})
        except ContributionStopIteration:
            if self._has_minimum_of_answers():
                self.erp.published = True
                self.erp.save()
            else:
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    translate(
                        "Vous n'avez pas fourni assez d'infos d'accessibilité. Votre établissement ne peut pas être publié."
                    ),
                )
            return reverse(self.success_route_name, kwargs={"erp_slug": self.erp.slug})

    def _get_section_number(self):
        done_mandatory_questions = [q for q in self.question_set[: self.step] if q.display_conditions == []]
        return len(done_mandatory_questions) + 1

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["erp"] = self.erp
        context["step"] = self._get_section_number()
        context["nb_sections"] = len([q for q in self.question_set if q.display_conditions == []]) + 1
        context["unsure_answer"] = UNSURE_ANSWER
        try:
            question_number = get_previous_question_number(self.step, erp=self.erp, questions=self.question_set)
            url = reverse(self.route_name, kwargs={"erp_slug": self.erp.slug, "step_number": question_number})
            context["previous_url"] = url
        except ContributionStopIteration:
            pass
        return context


class ContributionStepView(ContributionStepMixin):
    template_name = "contrib/contribution-step.html"
    question_set = CONTRIBUTION_QUESTIONS
    route_name = "contribution-step"
    success_route_name = "contribution-base-success"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        if self.step < 7:
            context["step_name"] = translate("L'entrée")
        elif self.step < 9:
            context["step_name"] = translate("L'accueil")
        elif self.step < 12:
            context["step_name"] = translate("Le stationnement")
        elif self.step < 14:
            context["step_name"] = translate("Les chambres")
        else:
            context["step_name"] = translate("Les équipements")
        return context


class AdditionalContributionStepView(ContributionStepMixin):
    template_name = "contrib/contribution-step.html"
    question_set = ADDITIONAL_CONTRIBUTION_QUESTIONS
    route_name = "contribution-additional-step"
    success_route_name = "contribution-additional-success"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        if self.step == 0:
            context["step_name"] = translate("Transport en commun")
        elif self.step < 5:
            context["step_name"] = translate("Chemin d'accès")
        elif self.step < 8:
            context["step_name"] = translate("Entrée")
        elif self.step < 12:
            context["step_name"] = translate("Chemin entre l'entrée et l'accueil")
        elif self.step < 14:
            context["step_name"] = translate("Les chambres")
        elif self.step < 16:
            context["step_name"] = translate("Equipements et prestations")
        elif self.step < 18:
            context["step_name"] = translate("Signalétique")
        else:
            context["step_name"] = translate("Autres")
        return context


def contribution_base_success_view(request, erp_slug):
    return render(
        request,
        "contrib/contribution-base-success.html",
        context={"erp": get_object_or_404(Erp, slug=erp_slug)},
    )


def contribution_additional_success_view(request, erp_slug):
    return render(
        request,
        "contrib/contribution-additional-success.html",
        context={"erp": get_object_or_404(Erp, slug=erp_slug)},
    )
