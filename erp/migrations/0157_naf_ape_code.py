# Generated by Django 4.2.1 on 2023-07-17 08:49

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("erp", "0156_translate_activity"),
    ]

    operations = [
        migrations.AddField(
            model_name="activite",
            name="naf_ape_code",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=10),
                blank=True,
                default=list,
                help_text="Liste des codes NAF/APE liés à cette activité, cf https://www.insee.fr/fr/information/2120875",
                null=True,
                size=None,
                verbose_name="Code NAF/APE",
            ),
        ),
    ]