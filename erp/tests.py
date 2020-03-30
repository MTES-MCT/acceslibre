from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.test import TestCase

from .forms import AdminErpForm


class AdminErpFormTestCase(TestCase):
    def test_invalid_on_empty_geocode_results(self):
        "Raise a validation error when address can't be geocoded"
        form = AdminErpForm(
            {
                "nom": "plop",
                "voie": "invalid",
                "code_postal": "XXXXX",
                "commune": "invalid",
            },
            geocode=lambda _: None,
        )
        self.assertFalse(form.is_valid())

    def test_valid_on_geocoded_results(self):
        form = AdminErpForm(
            {
                "nom": "plop",
                "numero": "4",
                "voie": "rue de la paix",
                "lieu_dit": "blah",
                "code_postal": "75000",
                "commune": "Paris",
            },
            geocode=lambda _: {
                "geom": Point((0, 0)),
                "numero": "4",
                "voie": "rue de la paix",
                "lieu_dit": "blah",
                "code_postal": "75000",
                "commune": "Paris",
                "code_insee": "75111",
            },
        )
        self.assertTrue(form.is_valid())
