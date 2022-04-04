import csv
import datetime
import os

from datetime import date
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.core.management.base import BaseCommand

# from erp.models import Erp


class Command(BaseCommand):
    help = "Exporte les utilisateurs ayant créé un compte sans jamais contribuer"

    def handle(self, *args, **options):
        User = get_user_model()
        users_having_no_erps = (
            User.objects.annotate(
                erp_count_total=Count("erp", distinct=True),
                erp_count_published=Count(
                    "erp",
                    filter=Q(
                        erp__published=True,
                        erp__accessibilite__isnull=False,
                        erp__geom__isnull=False,
                    ),
                    distinct=True,
                ),
            )
            .annotate(vote_count=Count("vote", distinct=True))
            .annotate(rev_count=Count("revision", distinct=True))
            .order_by("username")
        )
        stamp = date.today().isoformat()
        csv_filename = f"retargetting-{stamp}.csv"
        with open(os.path.join(settings.BASE_DIR, csv_filename), "w") as csvfile:
            fieldnames = [
                "username",
                "email",                "erp_count_published",
                "erp_count_total",
                "votes",
                "contributions",
                "last_login",
                "date_joined",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for user in users_having_no_erps.filter(
                erp_count_published=0, erp_count_total=0, rev_count=0
            ).filter(last_login__gte=datetime.date(2022, 1, 1)):
                writer.writerow(
                    {
                        "username": user.username,
                        "email": user.email,
                        "erp_count_published": user.erp_count_published,
                        "erp_count_total": user.erp_count_total,
                        "votes": user.vote_count,
                        "contributions": user.rev_count,
                        "last_login": user.last_login,
                        "date_joined": user.date_joined,
                    }
                )
