# TODO

# On prend un numéro d'étape et on gènère le form en question si c'est un get
# Si c'est un post on valide l'info et redirige


from django.views.generic.edit import FormView

from .forms import ContributionForm


class ContactFormView(FormView):
    template_name = "TODO.html"

    def get_form(self, form_class=None):
        # TODO get step number from URL
        # TODO get ERP ?
        return ContributionForm(question="TODO")
