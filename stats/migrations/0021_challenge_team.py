# Generated by Django 4.2.3 on 2024-04-04 08:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stats", "0020_remove_implem_widget_referer"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChallengeTeam",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(help_text="Nom de l'équipe", max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name="challengeplayer",
            name="team",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="players",
                to="stats.challengeteam",
                verbose_name="Challenge Team",
            ),
        ),
        migrations.AddField(
            model_name="challenge",
            name="classement_team",
            field=models.JSONField(default=dict),
        ),
    ]