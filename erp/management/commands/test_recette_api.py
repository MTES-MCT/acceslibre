import os

import requests
from django.core.management.base import BaseCommand, CommandError

DEFAULT_BASE_URL = "https://recette.acceslibre.info"
DEFAULT_SLUG = "chez-oim"
DEFAULT_TIMEOUT = 120
API_KEY_ENV_VAR = "ACCESLIBRE_RECETTE_API_KEY"

# Payload used to create the test ERP. The address is fictional: when the address
# cannot be geocoded, the API falls back on the given coordinates.
CREATE_PAYLOAD = {
    "activite": "Restaurant",
    "nom": "Chez Oim",
    "numero": "1",
    "voie": "rue de l'API Acceslibre",
    "code_postal": "75002",
    "commune": "Paris",
    "code_insee": "75056",
    "site_internet": "https://example.com",
    "contact_url": "https://example.com/contact",
    "latitude": 48.8698,
    "longitude": 2.307,
    "accessibilite": {
        "entree_reperage": True,
        "entree_porte_presence": True,
    },
}

# Payload used to update the test ERP. Only the accessibility data is editable.
UPDATE_PAYLOAD = {
    "accessibilite": {
        "stationnement_presence": True,
        "stationnement_pmr": True,
        "transport_station_presence": False,
    },
}


def find_value(payload, key):
    """Look for a key in a nested payload (the API groups the accessibility fields by section)."""
    if isinstance(payload, dict):
        for name, value in payload.items():
            if name == key:
                return value
            found = find_value(value, key)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = find_value(item, key)
            if found is not None:
                return found
    return None


class Command(BaseCommand):
    help = (
        "Smoke test the Acceslibre API of the recette environment. "
        "The creation and the update tests are run by default, use --skip-create and/or --skip-write to skip them."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--base-url",
            default=DEFAULT_BASE_URL,
            help="Base URL of the tested environment.",
        )
        parser.add_argument(
            "--slug",
            default=DEFAULT_SLUG,
            help="Slug of the ERP used by the write tests.",
        )
        parser.add_argument(
            "--skip-create",
            action="store_true",
            help="Skip the creation test (no POST, the database is left untouched).",
        )
        parser.add_argument(
            "--skip-write",
            action="store_true",
            help="Skip the update test (no PATCH, the accessibility data is left untouched).",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=DEFAULT_TIMEOUT,
            help="Timeout (in seconds) of each request.",
        )

    def handle(self, *args, **options):
        self.base_url = options["base_url"].rstrip("/")
        self.slug = options["slug"]
        self.timeout = options["timeout"]
        self.api_key = os.environ.get(API_KEY_ENV_VAR)
        self.failures = []
        self.snapshot = {}

        if not self.api_key:
            raise CommandError(f"No API key found: set the {API_KEY_ENV_VAR} environment variable.")

        self.stdout.write(f"Testing the API of {self.base_url} (ERP: {self.slug})")

        self.test_public_endpoints()
        self.test_authentication()
        self.test_read_endpoints()
        self.test_write_endpoints(
            create=not options["skip_create"],
            write=not options["skip_write"],
        )

        self.report()

    def test_public_endpoints(self):
        self._check("GET /api/ (public root)", (200,), "GET", "/api/", authenticated=False)
        self._check("GET /api/activites/ (public)", (200,), "GET", "/api/activites/?page_size=1", authenticated=False)
        self._check(
            "GET /api/accessibilite/help/ (public)",
            (200,),
            "GET",
            "/api/accessibilite/help/",
            authenticated=False,
        )

    def test_authentication(self):
        self._check(
            "GET /api/erps/ without API key is refused",
            (403,),
            "GET",
            "/api/erps/?page_size=1",
            authenticated=False,
        )
        self._check("GET /api/erps/ with API key", (200,), "GET", "/api/erps/?page_size=1")

    def test_read_endpoints(self):
        response = self._check(
            f"GET /api/erps/{self.slug}/",
            (200, 404),
            "GET",
            f"/api/erps/{self.slug}/",
        )
        if response is not None and response.status_code == 404:
            message = f"  ERP « {self.slug} » does not exist yet (it is created by the --create test)."
            self.stdout.write(self.style.WARNING(message))

        self._check(
            f"GET /api/erps/{self.slug}/widget/",
            (200, 404),
            "GET",
            f"/api/erps/{self.slug}/widget/",
        )

    def test_write_endpoints(self, create=True, write=True):
        if not create and not write:
            self.stdout.write("Write tests skipped (--skip-create and --skip-write).")
            return

        created = False
        if create:
            created = self.create_erp()
            if created is None:
                return

        if not write:
            return

        if created:
            payload = UPDATE_PAYLOAD
        else:
            response = self._check(
                f"GET /api/erps/{self.slug}/ (target ERP)",
                (200,),
                "GET",
                f"/api/erps/{self.slug}/",
            )
            if response is None:
                message = "  The target ERP does not exist: remove --skip-create to create it."
                self.stdout.write(self.style.WARNING(message))
                return
            self.snapshot = self._extract_values(response, UPDATE_PAYLOAD["accessibilite"].keys())
            payload = self._build_update_payload()

        if payload["accessibilite"]:
            self._check(
                f"PATCH /api/erps/{self.slug}/ (update)",
                (200,),
                "PATCH",
                f"/api/erps/{self.slug}/",
                json=payload,
            )
            response = self._check(
                f"GET /api/erps/{self.slug}/ (read after update)",
                (200,),
                "GET",
                f"/api/erps/{self.slug}/",
            )
            if response is not None:
                self._check_values("the accessibility data has been updated", response, payload["accessibilite"])

        self._check(
            f"PATCH /api/erps/{self.slug}/ without API key is refused",
            (403,),
            "PATCH",
            f"/api/erps/{self.slug}/",
            json=payload,
            authenticated=False,
        )

        if self.snapshot:
            self.restore_erp()

    def create_erp(self):
        """Create the test ERP. Returns True if it has been created, False if it already exists."""
        response = self._check(
            "POST /api/erps/ (create)",
            (201, 400),
            "POST",
            "/api/erps/",
            json=CREATE_PAYLOAD,
        )
        if response is None:
            return None

        if response.status_code == 400:
            details = self._details(response)
            message = f"  The creation has been refused, the ERP may already exist: {details}"
            self.stdout.write(self.style.WARNING(message))
            return False

        slug = response.json().get("slug")
        if slug:
            self.slug = slug

        url = f"{self.base_url}/admin/erp/erp/?q=Chez+Oim"
        message = f"  The created ERP « {self.slug} » has to be deleted manually (no DELETE endpoint): {url}"
        self.stdout.write(self.style.WARNING(message))
        return True

    def _build_update_payload(self):
        if not self.snapshot:
            return UPDATE_PAYLOAD

        values = {}
        untouched = []
        for field, value in UPDATE_PAYLOAD["accessibilite"].items():
            if self.snapshot.get(field) is None:
                untouched.append(field)
            else:
                values[field] = value

        if untouched:
            details = ", ".join(untouched)
            message = f"  Fields left untouched (empty initial value, not restorable): {details}"
            self.stdout.write(self.style.WARNING(message))

        return {"accessibilite": values}

    def restore_erp(self):
        values = {field: value for field, value in self.snapshot.items() if value is not None}
        if not values:
            return

        self._check(
            f"PATCH /api/erps/{self.slug}/ (restore the initial values)",
            (200,),
            "PATCH",
            f"/api/erps/{self.slug}/",
            json={"accessibilite": values},
        )

    def report(self):
        if self.failures:
            raise CommandError(f"{len(self.failures)} test(s) failed: {'; '.join(self.failures)}")

        self.stdout.write(self.style.SUCCESS("All the tests passed."))

    def _check(self, label, expected_statuses, method, path, *, json=None, authenticated=True):
        url = f"{self.base_url}{path}"
        headers = {"Accept": "application/json"}
        if authenticated:
            headers["Authorization"] = f"Api-Key {self.api_key}"

        try:
            response = requests.request(
                method,
                url,
                json=json,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as error:
            self._fail(label, f"request error: {error}")
            return None

        if response.status_code not in expected_statuses:
            self._fail(label, f"unexpected status {response.status_code}: {self._details(response)}")
            return None

        self.stdout.write(self.style.SUCCESS(f"OK   {label} (HTTP {response.status_code})"))
        return response

    def _check_values(self, label, response, expected_values):
        try:
            data = response.json()
        except ValueError:
            self._fail(label, "the response is not a JSON document")
            return

        accessibilite = data.get("accessibilite") or {}
        for field, expected in expected_values.items():
            value = find_value(accessibilite, field)
            if value != expected:
                self._fail(label, f"expected {field}={expected}, got {value}")
                return

        details = ", ".join(f"{field}={value}" for field, value in expected_values.items())
        self.stdout.write(self.style.SUCCESS(f"OK   {label} ({details})"))

    def _extract_values(self, response, fields):
        try:
            data = response.json()
        except ValueError:
            return {}

        accessibilite = data.get("accessibilite") or {}
        return {field: find_value(accessibilite, field) for field in fields}

    def _fail(self, label, details):
        self.stdout.write(self.style.ERROR(f"FAIL {label}: {details}"))
        self.failures.append(f"{label} ({details})")

    @staticmethod
    def _details(response):
        try:
            return str(response.json())[:300]
        except ValueError:
            return response.text[:300]
