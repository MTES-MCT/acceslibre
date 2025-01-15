from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.sitemaps import StaticViewSitemap


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /compte/*",
        "",
        f"Sitemap: {settings.SITE_ROOT_URL}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def html_sitemap(request):
    sitemap_instance = StaticViewSitemap()
    sitemap_urls = [
        {
            "location": sitemap_instance.location(item),
            "title": sitemap_instance.title(item),
        }
        for item in sitemap_instance.items()
    ]
    return render(request, "sitemap.html", {"sitemap_urls": sitemap_urls})
