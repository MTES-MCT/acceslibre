# Generated by Django 3.2.18 on 2023-03-23 14:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("erp", "0153_translation"),
    ]

    operations = [
        migrations.CreateModel(
            name="ActivitiesGroup",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="Nom du groupe d'activités", max_length=255)),
                ("activities", models.ManyToManyField(related_name="groups", to="erp.Activite")),
            ],
        ),
    ]
