"""
ASGI config for access4all project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "access4all.settings")

# Detect Scalingo environment
if "SCALINGO_POSTGRESQL_URL" in os.environ:
    from dj_static import Cling

    application = Cling(get_wsgi_application())
else:
    application = get_asgi_application()
