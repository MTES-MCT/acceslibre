import copy

from django.contrib.admin.models import LogEntry, ADDITION
from django.views.generic import TemplateView
from django.utils import timezone

from erp.models import Commune, Erp


class StatsView(TemplateView):
    template_name = "stats/index.html"

    def get_nb_contributors(self):
        return (
            LogEntry.objects.order_by("user")
            .filter(action_flag=ADDITION, content_type__model="erp")
            .distinct("user")
            .count()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        erp_qs = Erp.objects.published()

        context["nb_published_erps"] = erp_qs.count()
        context["nb_filled_erps"] = erp_qs.having_an_accessibilite().count()
        context["communes"] = Commune.objects.erp_stats()[:8]
        context["nb_contributors"] = self.get_nb_contributors()

        return context
