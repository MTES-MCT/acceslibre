import json

from django import forms
from django.utils.translation import gettext_lazy as translate_lazy

from erp.models import Activite


class ActivityField(forms.CharField):
    @property
    def _get_search_lookup(self):
        queryset = Activite.objects.order_by("position")
        search_lookup = [{"name": a.nom, "keywords": a.keyword_with_name} for a in queryset]
        return json.dumps(search_lookup)

    def __init__(self, **kwargs):
        super().__init__(
            label=translate_lazy("Activité"),
            required=True,
            **kwargs,
            widget=forms.TextInput(
                attrs={
                    "class": "fr-input",
                    "data-search-lookup": self._get_search_lookup,
                    "placeholder": translate_lazy("Cinéma, mairie, ..."),
                }
            ),
        )
