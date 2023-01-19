from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        f"Sitemap: {settings.SITE_ROOT_URL}/sitemap.xml",
        "Crawl-delay: 1",
        "",
        "User-agent: PetalBot",
        "Disallow: /",
        "",
        "User-agent: Screaming Frog SEO Spider",
        "Disallow: /",
        "",
        "User-agent: AhrefsBot",
        "Disallow: /",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
