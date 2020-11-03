from django.contrib.sitemaps import Sitemap

from erp.models import Commune, Erp

# changefresq values: always, hourly, daily, weekly, monthly, yearly, never


class CommuneSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5
    limit = 10000

    def items(self):
        return Commune.objects.having_published_erps()

    def lastmod(self, obj):
        return obj.updated_at


class ErpSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.6
    limit = 10000

    def items(self):
        return Erp.objects.published()

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {"communes": CommuneSitemap, "erps": ErpSitemap}
