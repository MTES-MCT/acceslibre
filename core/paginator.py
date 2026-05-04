import hashlib

from django.core.cache import cache
from django.core.paginator import Paginator


class CachedCountPaginator(Paginator):
    def __init__(self, *args, cache_key=None, cache_timeout=300, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache_key = cache_key
        self._cache_timeout = cache_timeout

    @property
    def count(self):
        if self._cache_key is None:
            return super().count
        cached = cache.get(self._cache_key)
        if cached is not None:
            return cached
        count = super().count
        cache.set(self._cache_key, count, self._cache_timeout)
        return count

    @staticmethod
    def get_cache_key(request):
        filter_params = request.GET.copy()
        filter_params.pop("page", None)

        raw_key = f"erp_count_{filter_params.urlencode()}"
        return hashlib.md5(raw_key.encode()).hexdigest()
