from urllib.parse import urlparse

from dj_static import Cling as Static3Cling
from django.contrib.staticfiles.handlers import StaticFilesHandler as DebugHandler

import static


class Cling(Static3Cling):
    """
    On surcharge la librairie dj_static car elle ne prend pas en charge les headers que Cling peut accepter.
    Cela permet, dans un environnement scalingo par exemple, de controler les CORS sur les fichiers statiques qui
    sont, de fait, non géré par Django.

    Liens:
     * https://github.com/heroku-python/dj-static/blob/master/dj_static.py
     * https://github.com/rmohr/static3#serving-compressed-files
    """

    def __init__(self, application, base_dir=None, ignore_debug=False, headers=None):
        self.application = application
        self.ignore_debug = ignore_debug
        if not base_dir:
            base_dir = self.get_base_dir()
        self.base_url = urlparse(self.get_base_url())

        self.cling = static.Cling(base_dir, headers=headers)

        try:
            self.debug_cling = DebugHandler(application, base_dir=base_dir)
        except TypeError:
            self.debug_cling = DebugHandler(application)
