# Generated by Django 4.2.11 on 2024-05-07 09:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("compte", "0007_alter_userpreferences_newsletter_opt_in"),
    ]

    operations = [
        migrations.AddField(
            model_name="userstats",
            name="nb_erp_administrator",
            field=models.IntegerField(default=0),
        ),
    ]
