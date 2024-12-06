import json

from django import forms
from django.utils.translation import gettext_lazy as translate_lazy

from erp.models import Activite


class BaseActivityField:
    @property
    def _get_search_lookup(self):
        queryset = Activite.objects.order_by("position")
        search_lookup = [{"name": a.nom, "keywords": a.keyword_with_name, "slug": a.slug} for a in queryset]
        return json.dumps(search_lookup, ensure_ascii=False)

    def get_widget(self):
        return forms.TextInput(
            attrs={
                "class": "fr-input",
                "data-search-lookup": self._get_search_lookup,
                "placeholder": translate_lazy("Cinéma, mairie, ..."),
            }
        )


class ActivityCharField(BaseActivityField, forms.CharField):
    def __init__(self, **kwargs):
        super().__init__(
            label=translate_lazy("Activité"),
            required=True,
            widget=self.get_widget(),
            **kwargs,
        )


class ActivityField(BaseActivityField, forms.ModelChoiceField):
    def __init__(self, **kwargs):
        super().__init__(
            label=translate_lazy("Activité"),
            required=True,
            queryset=Activite.objects.order_by("position"),
            widget=self.get_widget(),
            to_field_name="nom",
            **kwargs,
        )
