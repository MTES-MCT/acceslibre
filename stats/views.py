from django.contrib.auth import get_user_model
from django.db.models import Count
from django.views.generic import TemplateView

from erp.models import Commune, Erp, Vote


class StatsView(TemplateView):
    template_name = "stats/index.html"

    def get_nb_contributors(self):
        return (
            Erp.objects.filter(accessibilite__isnull=False)
            .order_by("user")
            .distinct("user")
            .count()
        )

    def get_top_contributors(self):
        return (
            get_user_model()
            .objects.annotate(erp_count=Count("erp", distinct=True))
            .filter(erp__accessibilite__isnull=False)
            .order_by("-erp_count")[:10]
        )

    def get_top_voters(self):
        return (
            get_user_model()
            .objects.annotate(vote_count=Count("vote", distinct=True))
            .exclude(vote_count=0)
            .order_by("-vote_count")[:10]
        )

    def get_north_star(self):
        vote_qs = Vote.objects
        positive = vote_qs.filter(value=1).count()
        total = vote_qs.count()
        percent = (positive / total * 100) if total > 0 else 100
        return {
            "positive": positive,
            "total": total,
            "percent": percent,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        erp_qs = Erp.objects.published()

        context["north_star"] = self.get_north_star()
        context["nb_filled_erps"] = erp_qs.count()
        context["communes"] = Commune.objects.erp_stats()[:10]
        context["nb_contributors"] = self.get_nb_contributors()
        context["top_contributors"] = self.get_top_contributors()
        context["top_voters"] = self.get_top_voters()

        return context
