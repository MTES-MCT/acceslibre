import schedule
import time

from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from erp.models import Erp, StatusCheck
from erp import sirene

CHECK_DAYS = 7  # recheck activity status every 7 days
SIRENE_API_SLEEP = 0.5  # stay way under 500 req/s, which is our rate limit


def send_notification(erp):
    print(
        f"{erp.nom} à {erp.commune_ext.nom} est désormais fermé, envoi d'un email de notification"
    )
    send_mail(
        f"[{settings.SITE_NAME}] Établissement fermé : {erp.nom} à {erp.commune_ext.nom}",
        "\n\n".join(
            [
                f"Le registre SIRENE indique que l'établissement {erp.nom} à {erp.commune_ext.nom} est désormais fermé.",
                f"Fiche de l'établissement : {settings.SITE_ROOT_URL}{erp.get_absolute_url()}",
                "--\nLe gentil serveur Acceslibre",
            ]
        ),
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_FROM_EMAIL],
        fail_silently=True,
    )


def job():
    erps_to_check = (
        Erp.objects.published().filter(siret__isnull=False).order_by("updated_at")
    )
    print(
        f"Vérification du statut d'activité de {erps_to_check.count()} établissements"
    )
    for erp in erps_to_check:
        # discard invalid sirets
        if sirene.validate_siret(erp.siret) is None:
            # print(f"SKIP {erp.nom} {erp.siret}")
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
            send_notification(erp)
        time.sleep(SIRENE_API_SLEEP)


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        schedule.every(1).days.do(job)

        while True:
            schedule.run_pending()
            time.sleep(1)
