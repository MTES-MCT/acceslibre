from datetime import date

import redis
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError, models

from stats.models import WidgetDomain, WidgetEvent


class Command(BaseCommand):
    help = "Flush widget statistics from Redis to PostgreSQL"

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Print detailed information about the flush process",
        )

    def handle(self, *args, **options):
        verbose = options.get("verbose", False)
        cache_conf = settings.CACHES["default"]
        location = cache_conf["LOCATION"]

        r = redis.from_url(location)

        # Pattern to catch keys with or without Django's version prefix (:1:)
        pattern = "*stats_widget:*"

        keys_found = 0
        views_per_domain = {}
        if verbose:
            self.stdout.write(f"Scanning Redis with pattern: {pattern}")

        for key in r.scan_iter(pattern):
            key_str = key.decode("utf-8")

            # Atomic fetch and delete to prevent race conditions
            # We get the value and remove the key in a single transaction
            pipe = r.pipeline()
            pipe.get(key)
            pipe.delete(key)
            results = pipe.execute()

            val = results[0]
            if val is None:
                continue

            count = int(val)

            try:
                # We split after 'stats_widget:' to ignore any prefixes
                raw_data = key_str.split("stats_widget:")[1]

                # maxsplit=2 is crucial because referer_url contains colons (http://...)
                date_str, domain, referer = raw_data.split(":", 2)
                event_date = date.fromisoformat(date_str)

                updated = WidgetEvent.objects.filter(date=date_str, domain=domain, referer_url=referer).update(
                    views=models.F("views") + count
                )

                if not updated:
                    try:
                        WidgetEvent.objects.create(
                            date=date_str,
                            domain=domain,
                            referer_url=referer,
                            views=count,
                        )
                    except IntegrityError:
                        # Fallback: if another process created the row in the split second
                        # between update() and create(), we update it now.
                        WidgetEvent.objects.filter(date=date_str, domain=domain, referer_url=referer).update(
                            views=models.F("views") + count
                        )

                entry = views_per_domain.setdefault(
                    domain, {"first_seen": event_date, "last_seen": event_date, "views": 0}
                )
                entry["first_seen"] = min(entry["first_seen"], event_date)
                entry["last_seen"] = max(entry["last_seen"], event_date)
                entry["views"] += count

                keys_found += 1
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f"Flushed {count} views for {domain}"))

            except (IndexError, ValueError) as e:
                self.stdout.write(self.style.WARNING(f"Skipping malformed key {key_str}: {e}"))
                continue

        for domain, entry in views_per_domain.items():
            WidgetDomain.record(
                domain,
                first_seen=entry["first_seen"],
                last_seen=entry["last_seen"],
                total_views=entry["views"],
                accumulate=True,
            )

        self.stdout.write(self.style.SUCCESS(f"Successfully flushed {keys_found} entries to DB"))
