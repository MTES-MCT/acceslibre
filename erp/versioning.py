from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone
from reversion.models import Version

from .models import Accessibilite, Erp


def extract_online_erp(version):
    """Extract the Erp object from a reversion.models.Version instance,
    which can link either an Erp or an Accessibilite.
    """
    if not hasattr(version, "content_type"):
        return None

    if not version.object:
        return None

    erp = version.object if version.content_type == ContentType.objects.get_for_model(Erp) else version.object.erp
    if erp and erp.published:
        return erp
    else:
        return None


def get_user_contributions(user):
    erp_type = ContentType.objects.get_for_model(Erp)
    accessibilite_type = ContentType.objects.get_for_model(Accessibilite)
    user_erps = [f["id"] for f in Erp.objects.filter(user=user).values("id")]
    user_accesses = [f["id"] for f in Accessibilite.objects.filter(erp__user=user).values("id")]
    return (
        Version.objects.select_related("revision", "revision__user")
        .exclude(content_type=erp_type, object_id__in=user_erps)
        .exclude(content_type=accessibilite_type, object_id__in=user_accesses)
        .filter(revision__user=user, content_type__in=(erp_type, accessibilite_type))
        .prefetch_related("object")
        .order_by("-revision__date_created")
    )


def get_user_contributions_recues(user):
    erp_type = ContentType.objects.get_for_model(Erp)
    accessibilite_type = ContentType.objects.get_for_model(Accessibilite)
    user_erps = [f["id"] for f in Erp.objects.filter(user=user).values("id")]
    user_accesses = [f["id"] for f in Accessibilite.objects.filter(erp__user=user).values("id")]
    return (
        Version.objects.select_related("revision", "revision__user")
        .exclude(Q(revision__user=user) | Q(revision__user__isnull=True))
        .filter(
            Q(content_type=erp_type, object_id__in=user_erps)
            | Q(content_type=accessibilite_type, object_id__in=user_accesses),
        )
        .prefetch_related("object")
        .order_by("-revision__date_created")
    )


def get_recent_contribs_qs(hours, now=None):
    "Retrieves Erp and Accessibilite versions created since a given number of hours."
    now = now or timezone.now()
    erp_type = ContentType.objects.get_for_model(Erp)
    accessibilite_type = ContentType.objects.get_for_model(Accessibilite)
    return (
        Version.objects.select_related("revision", "revision__user")
        .exclude(revision__user__isnull=True)
        .exclude(content_type__isnull=True)
        .filter(Q(content_type=erp_type) | Q(content_type=accessibilite_type))
        .filter(revision__date_created__gt=now - timedelta(hours=hours))
        .prefetch_related("object")
    )


def get_previous_version(version):
    return (
        Version.objects.filter(
            revision__date_created__lt=version.revision.date_created,
            content_type_id=version.content_type_id,
            object_id=version.object_id,
        )
        .order_by("-revision__date_created")
        .first()
    )
