from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        f"Sitemap: {settings.SITE_ROOT_URL}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
