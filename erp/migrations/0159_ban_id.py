# Generated by Django 4.2.3 on 2023-11-21 16:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("erp", "0158_add_source_outscraper"),
    ]

    operations = [
        migrations.AddField(
            model_name="erp",
            name="ban_id",
            field=models.CharField(
                blank=True,
                help_text="Identifiant de la BAN",
                max_length=50,
                null=True,
                verbose_name="identifiant BAN",
            ),
        ),
    ]
