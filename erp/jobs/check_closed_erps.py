import logging
import time

from datetime import date, timedelta

from django.conf import settings
from django.utils import timezone

from core import mailer

from erp.models import Erp, StatusCheck
from erp.provider import sirene


logger = logging.getLogger(__name__)

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


def unpublish_closed_erp(erp, closed_on):
    if not closed_on:
        return
    try:
        closed_on_day = date.fromisoformat(closed_on)
        today = date.today()
        if today - closed_on_day > timedelta(days=365):
            erp.published = False
            erp.save()
            logger.info(
                f"{erp.nom} est fermé depuis le {closed_on} et a été mis hors-ligne."
            )
            return erp
    except ValueError:
        return


def get_closed_erps():  # noqa
    closed_erps = []
    erps_to_check = (
        Erp.objects.published().filter(siret__isnull=False).order_by("updated_at")
    )
    logger.debug(f"[INFO] Checking {erps_to_check.count()} erps")
    for erp in erps_to_check:
        # discard invalid sirets
        if sirene.validate_siret(erp.siret) is None:
            logger.debug(f"[SKIP] Invalid siret {erp.nom} {erp.siret}")
            continue
        check = StatusCheck.objects.filter(erp=erp).first()
        if check and check.non_diffusable:
            continue
        # check last check timestamp
        if check and timezone.now() < check.last_checked + timedelta(days=CHECK_DAYS):
            continue
        # process check
        active = True
        non_diffusable = False
        closed_on = None
        try:
            infos = sirene.get_siret_info(erp.siret)
            active = infos.get("actif", True)
            closed_on = infos.get("closed_on")
        except RuntimeError as err:
            logger.warn(f"Établissement {erp.nom} ({erp.siret}): {err}")
            if "non diffusable" in str(err):
                non_diffusable = True
                logger.debug("Les informations de cet ERP ne sont pas diffusables.")
        if not check:
            check = StatusCheck(erp=erp)
        check.non_diffusable = non_diffusable
        check.active = active
        check.save()
        if not active:
            logger.debug(f"[WARN] {erp.nom} is closed, sending notification")
            closed_erp = unpublish_closed_erp(erp, closed_on)
            if closed_erp:
                closed_erps.append(erp)
        else:
            logger.debug(f"[PASS] {erp.nom} is active")
        time.sleep(SIRENE_API_SLEEP)
    return closed_erps


def job(*args, **kwargs):
    closed_erps = get_closed_erps()
    if len(closed_erps) > 0:
        logger.debug("[DONE] Check complete, sending a report.")
        send_report(closed_erps)
    else:
        logger.debug("[DONE] Check complete, no reports to send.")
