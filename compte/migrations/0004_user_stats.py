# Generated by Django 3.2.18 on 2023-02-20 10:07

import django.db.models.deletion
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import migrations, models
from django.db.models import Count, F
from reversion.models import Revision

from compte.models import UserStats
from erp.models import Erp


def populate_initial_user_stats(apps, schema_editor):
    # NOTE: the following is taking too long and causing a timeout on deploy. Has to be manually launched
    #       in a detached container
    return

    for data in (
        Erp.objects.filter(user_id__isnull=False)
        .values("user_id")
        .annotate(total=Count("user_id"))
        .filter(total__gt=0)
        .values("user_id", "total")
    ):
        try:
            user = get_user_model().objects.get(pk=data["user_id"])
        except get_user_model().DoesNotExist:
            continue
        user_stats, _ = UserStats.objects.get_or_create(user=user)
        user_stats.nb_erp_created = F("nb_erp_created") + data["total"]
        user_stats.save()

    for data in (
        Revision.objects.filter(user_id__isnull=False)
        .values("user_id")
        .annotate(total=Count("user_id"))
        .filter(total__gt=0)
        .values("user_id", "total")
    ):
        try:
            user = get_user_model().objects.get(pk=data["user_id"])
        except get_user_model().DoesNotExist:
            continue
        user_stats, _ = UserStats.objects.get_or_create(user=user)
        user_stats.nb_erp_edited = F("nb_erp_edited") + data["total"]
        user_stats.save()


def backwards(*args, **kwargs):
    ...


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency("erp.Erp"),
        migrations.swappable_dependency("reversion.Revision"),
        ("compte", "0003_auto_20210701_1337"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserStats",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nb_erp_created", models.IntegerField(default=0)),
                ("nb_erp_edited", models.IntegerField(default=0)),
                ("nb_erp_attributed", models.IntegerField(default=0)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stats",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Utilisateur",
                    ),
                ),
            ],
            options={
                "verbose_name": "UserStats",
                "verbose_name_plural": "UsersStats",
            },
        ),
        migrations.RunPython(populate_initial_user_stats, backwards),
    ]
