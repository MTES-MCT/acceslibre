"""
WSGI config.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from core.lib.wsgi import Cling

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_prod")

headers = [
    {"prefix": "", "Access-Control-Allow-Origin": "*"},
]

application = Cling(get_wsgi_application(), headers=headers)
