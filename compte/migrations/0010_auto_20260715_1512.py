import logging
import re

from django.db import migrations
from django.utils import timezone

logger = logging.getLogger("api_keys_migration")

EMAIL_RE = re.compile(r"[\w\.\-+]+@[\w\-]+\.[\w\.\-]+")


def migrate_legacy_keys(apps, schema_editor):
    APIKey = apps.get_model("rest_framework_api_key", "APIKey")
    UserAPIKey = apps.get_model("compte", "UserAPIKey")
    User = apps.get_model(*settings_auth_user_model(apps))

    now = timezone.now()

    stats = {"migrated": 0, "no_email_found": 0, "no_user_match": 0, "ambiguous": 0, "skipped_state": 0}

    for key in APIKey.objects.all():
        if key.revoked:
            stats["skipped_state"] += 1
            continue
        if key.expiry_date is not None and key.expiry_date <= now:
            stats["skipped_state"] += 1
            continue

        match = EMAIL_RE.search(key.name or "")
        if not match:
            stats["no_email_found"] += 1
            logger.warning("No email found in key name: prefix=%s name=%r", key.prefix, key.name)
            continue

        email = match.group(0)
        users = list(User.objects.filter(email__iexact=email))

        if len(users) == 0:
            stats["no_user_match"] += 1
            logger.warning("No user found for email=%s (key prefix=%s)", email, key.prefix)
            continue

        if len(users) > 1:
            stats["ambiguous"] += 1
            logger.warning("Multiple users found for email=%s (key prefix=%s), skipping", email, key.prefix)
            continue

        user = users[0]

        UserAPIKey.objects.create(
            id=key.id,
            prefix=key.prefix,
            hashed_key=key.hashed_key,
            created=key.created,
            name=key.name,
            revoked=key.revoked,
            expiry_date=key.expiry_date,
            user=user,
        )

        key.revoked = True
        key.save(update_fields=["revoked"])

        stats["migrated"] += 1

    logger.info("Legacy API key migration done: %s", stats)


def settings_auth_user_model(apps):
    from django.conf import settings

    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    return app_label, model_name


def reverse_migration(apps, schema_editor):
    APIKey = apps.get_model("rest_framework_api_key", "APIKey")
    UserAPIKey = apps.get_model("compte", "UserAPIKey")

    migrated_ids = list(UserAPIKey.objects.values_list("id", flat=True))
    APIKey.objects.filter(id__in=migrated_ids).update(revoked=False)
    UserAPIKey.objects.filter(id__in=migrated_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("compte", "0009_userapikey"),
        ("rest_framework_api_key", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(migrate_legacy_keys, reverse_migration),
    ]
