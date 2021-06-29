from django.contrib.auth import get_user_model
from django.db import migrations

from compte.models import UserPreferences


def migrate_prestations_to_commentaire(apps, schema_editor):
    users = get_user_model().objects.all()
    for user in users:
        UserPreferences.objects.create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ("compte", "0002_userpreferences"),
    ]

    operations = [
        migrations.RunPython(migrate_prestations_to_commentaire),
    ]
