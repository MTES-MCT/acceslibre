from django.views.generic import TemplateView

from erp.models import Commune, Erp


class StatsView(TemplateView):
    template_name = "stats/index.html"

    def get_nb_contributors(self):
        return (
            Erp.objects.filter(accessibilite__isnull=False)
            .order_by("user")
            .distinct("user")
            .count()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        erp_qs = Erp.objects.published()

        context["nb_published_erps"] = erp_qs.count()
        context["nb_filled_erps"] = erp_qs.having_an_accessibilite().count()
        context["communes"] = Commune.objects.erp_stats()[:10]
        context["nb_contributors"] = self.get_nb_contributors()

        return context
