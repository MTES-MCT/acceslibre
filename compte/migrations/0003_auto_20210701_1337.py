from django.contrib.auth import get_user_model
from django.db import migrations

from compte.models import UserPreferences


def add_preferences_to_users(apps, schema_editor):
    users = get_user_model().objects.all()
    for user in users:
        UserPreferences.objects.create(user=user)


class Migration(migrations.Migration):
    dependencies = [
        ("compte", "0002_userpreferences"),
    ]

    operations = [
        migrations.RunPython(add_preferences_to_users),
    ]
