from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from erp.models import Commune, Erp

# changefresq values: always, hourly, daily, weekly, monthly, yearly, never


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return ["home", "cgu", "accessibilite", "partenaires"]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1 if item == "home" else 0.5


class CommuneSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    limit = 10000

    def items(self):
        return Commune.objects.having_published_erps()

    def lastmod(self, obj):
        return obj.updated_at


class ErpSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    limit = 10000

    def items(self):
        return Erp.objects.published()

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {
    "static": StaticViewSitemap,
    "communes": CommuneSitemap,
    "erps": ErpSitemap,
}
