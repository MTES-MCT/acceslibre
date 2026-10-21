from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from stats.models import WidgetDomainMonth, WidgetEvent


class Command(BaseCommand):
    help = "Rebuild the WidgetDomainMonth aggregates from the WidgetEvent history (idempotent)"

    def handle(self, *args, **options):
        # Strip any ordering so it cannot be injected in the GROUP BY.
        aggregates = (
            WidgetEvent.objects.values("domain", month=TruncMonth("date")).annotate(total_views=Sum("views")).order_by()
        )

        backfilled = 0
        for aggregate in aggregates.iterator():
            WidgetDomainMonth.record(
                aggregate["domain"],
                month=aggregate["month"],
                total_views=aggregate["total_views"],
                accumulate=False,
            )
            backfilled += 1

        self.stdout.write(self.style.SUCCESS(f"Backfilled {backfilled} domain months"))
        self.stdout.write(f"WidgetDomainMonth rows: {WidgetDomainMonth.objects.count()}")
