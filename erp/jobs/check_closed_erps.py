import time

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from core import mailer

from erp.models import Erp, StatusCheck
from erp import sirene

CHECK_DAYS = 7  # recheck activity status every 7 days
SIRENE_API_SLEEP = 0.5  # stay way under 500 req/s, which is our rate limit


def send_report(closed_erps):
    mailer.mail_admins(
        f"[{settings.SITE_NAME}] Rapport quotidien de vérification de statut d'activité SIRENE",
        "mail/closed_erps_notification.txt",
        {
            "closed_erps": closed_erps,
            "SITE_NAME": settings.SITE_NAME,
            "SITE_ROOT_URL": settings.SITE_ROOT_URL,
        },
    )


def get_closed_erps(log):
    closed_erps = []
    erps_to_check = (
        Erp.objects.published().filter(siret__isnull=False).order_by("updated_at")
    )
    log(f"[INFO] Checking {erps_to_check.count()} erps")
    for erp in erps_to_check:
        # discard invalid sirets
        if sirene.validate_siret(erp.siret) is None:
            log(f"[SKIP] Invalid siret {erp.nom} {erp.siret}")
            continue
        check = StatusCheck.objects.filter(erp=erp).first()
        # check last check timestamp
        if check and timezone.now() < check.last_checked + timedelta(days=CHECK_DAYS):
            continue
        # process check
        try:
            infos = sirene.get_siret_info(erp.siret)
        except RuntimeError:
            continue
        if not check:
            check = StatusCheck(erp=erp)
        check.active = infos.get("actif", True)
        check.save()
        if not check.active:
            log(f"[WARN] {erp.nom} is closed, sending notification")
            closed_erps.append(erp)
        else:
            log(f"[PASS] {erp.nom} is active")
        time.sleep(SIRENE_API_SLEEP)
    return closed_erps


def job(*args, **kwargs):
    def log(msg):
        if kwargs.get("verbose", False):
            print(msg)

    closed_erps = get_closed_erps(log)
    if len(closed_erps) > 0:
        log("[DONE] Check complete, sending a report.")
        send_report(closed_erps)
    else:
        log("[DONE] Check complete, no reports to send.")
