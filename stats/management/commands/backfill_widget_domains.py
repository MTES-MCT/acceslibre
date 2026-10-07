from django.core.management.base import BaseCommand
from django.db.models import Max, Min, Sum

from stats.models import WidgetDomain, WidgetEvent


class Command(BaseCommand):
    help = "Rebuild the WidgetDomain aggregates from the WidgetEvent history (idempotent)"

    def handle(self, *args, **options):
        # Meta.ordering would be injected in the GROUP BY, drop it.
        aggregates = (
            WidgetEvent.objects.values("domain")
            .annotate(first_seen=Min("date"), last_seen=Max("date"), total_views=Sum("views"))
            .order_by()
        )

        backfilled = 0
        for aggregate in aggregates.iterator():
            WidgetDomain.record(
                aggregate["domain"],
                first_seen=aggregate["first_seen"],
                last_seen=aggregate["last_seen"],
                total_views=aggregate["total_views"],
                accumulate=False,
            )
            backfilled += 1

        self.stdout.write(self.style.SUCCESS(f"Backfilled {backfilled} domains"))
        self.stdout.write(f"WidgetDomain rows: {WidgetDomain.objects.count()}")
