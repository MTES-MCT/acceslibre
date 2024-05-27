from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from erp.models import Commune, Erp
from erp.provider import departements

# changefresq values: always, hourly, daily, weekly, monthly, yearly, never


class AnnuaireSitemap(Sitemap):
    changefreq = "weekly"
    protocol = "https"
    priority = 0.5
    limit = 10000

    def items(self):
        return list(departements.DEPARTEMENTS.keys())

    def location(self, item):
        return reverse("annuaire_departement", kwargs={"departement": item})


class CommuneSitemap(Sitemap):
    changefreq = "weekly"
    protocol = "https"
    priority = 0.6
    limit = 1000

    def items(self):
        return Commune.objects.having_published_erps().only("slug")

    def lastmod(self, obj):
        return obj.updated_at

    def get_latest_lastmod(*args, **kwargs):
        return Commune.objects.having_published_erps().first().updated_at


class ErpSitemap(Sitemap):
    changefreq = "daily"
    protocol = "https"
    priority = 0.8
    limit = 1000

    def items(self):
        return Erp.objects.published().select_related("activite")

    def lastmod(self, obj):
        return obj.updated_at

    def get_latest_lastmod(*args, **kwargs):
        return Erp.objects.published().order_by("-updated_at").first().updated_at


class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    protocol = "https"

    def items(self):
        return [
            ("home", 1),
            ("communes", 0.9),
            ("apidocs", 0.8),
            ("mentions-legales", 0.5),
            ("accessibilite", 0.5),
            ("partenaires", 0.4),
            ("stats_home", 0.1),
        ]

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):
        return item[1]


SITEMAPS = {
    "annuaire": AnnuaireSitemap,
    "communes": CommuneSitemap,
    "erps": ErpSitemap,
    "static": StaticViewSitemap,
}
