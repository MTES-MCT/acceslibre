from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from erp.models import Commune, Erp

# changefresq values: always, hourly, daily, weekly, monthly, yearly, never


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return [
            ("home", 1),
            ("apidocs", 0.8),
            ("cgu", 0.5),
            ("accessibilite", 0.5),
            ("partenaires", 0.4),
            ("stats", 0.1),
        ]

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):
        return item[1]


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
