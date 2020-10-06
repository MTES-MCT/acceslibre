from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone

from reversion.models import Version

from .models import Accessibilite, Erp


def get_user_contributions(user):
    erp_type = ContentType.objects.get_for_model(Erp)
    accessibilite_type = ContentType.objects.get_for_model(Accessibilite)
    user_erps = [f["id"] for f in Erp.objects.filter(user=user).values("id")]
    user_accesses = [
        f["id"] for f in Accessibilite.objects.filter(erp__user=user).values("id")
    ]
    return (
        Version.objects.select_related("revision", "revision__user")
        .exclude(content_type=erp_type, object_id__in=user_erps)
        .exclude(content_type=accessibilite_type, object_id__in=user_accesses)
        .filter(
            Q(revision__user=user),
            Q(content_type=erp_type) | Q(content_type=accessibilite_type),
        )
        .prefetch_related("object")
    )


def get_user_contributions_recues(user):
    erp_type = ContentType.objects.get_for_model(Erp)
    accessibilite_type = ContentType.objects.get_for_model(Accessibilite)
    user_erps = [f["id"] for f in Erp.objects.filter(user=user).values("id")]
    user_accesses = [
        f["id"] for f in Accessibilite.objects.filter(erp__user=user).values("id")
    ]
    return (
        Version.objects.select_related("revision", "revision__user")
        .exclude(Q(revision__user=user) | Q(revision__user__isnull=True))
        .filter(
            Q(content_type=erp_type) | Q(content_type=accessibilite_type),
            Q(content_type=erp_type, object_id__in=user_erps)
            | Q(content_type=accessibilite_type, object_id__in=user_accesses),
        )
        .prefetch_related("object")
    )


def get_recent_contribs(hours, now=None):
    now = now or timezone.now()
    "Retrieves erps updated by other users than their owner since a given number of hours."
    erp_type = ContentType.objects.get_for_model(Erp)
    accessibilite_type = ContentType.objects.get_for_model(Accessibilite)
    versions = (
        Version.objects.get_for_model(Erp)
        .select_related("revision", "revision__user")
        .exclude(revision__user__isnull=True)
        .exclude(content_type__isnull=True)
        .filter(Q(content_type=erp_type) | Q(content_type=accessibilite_type))
        .filter(revision__date_created__gt=now - timedelta(hours=hours))
        .prefetch_related("object")
    )
    changed = []
    for version in versions:
        # how is this supposed to happen? because it does.
        if not hasattr(version, "content_type"):
            continue
        erp = (
            version.object
            if version.content_type == erp_type
            else version.object.accessibilite
        )
        owner = erp.user
        modified_by_other = owner and owner.id != version.revision.user_id
        if erp and erp.user and modified_by_other and erp not in changed:
            changed.append({"erp": erp, "contributor": version.revision.user})
    return changed


def get_owners_to_notify(hours, now=None):
    recent_contribs = get_recent_contribs(hours, now)
    owners = {}
    for change in recent_contribs:
        owner_pk = change["erp"].user.pk
        if owner_pk not in owners:
            owners[owner_pk] = []
        owners[owner_pk].append(change)
    return owners
