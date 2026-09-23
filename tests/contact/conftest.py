import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def reset_contact_ratelimit():
    cache.clear()
