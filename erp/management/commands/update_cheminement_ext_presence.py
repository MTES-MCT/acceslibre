from erp.models import Accessibilite
from django.core.management.base import BaseCommand

fields = [
    "cheminement_ext_plain_pied",
    "cheminement_ext_nombre_marches",
    "cheminement_ext_reperage_marches",
    "cheminement_ext_main_courante",
    "cheminement_ext_rampe",
    "cheminement_ext_ascenseur",
    "cheminement_ext_pente",
    "cheminement_ext_devers",
    "cheminement_ext_bande_guidage",
    "cheminement_ext_retrecissement",
]


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        lst = Accessibilite.objects.all()
        for accessibilite in lst:
            filled = any(getattr(accessibilite, f) is not None for f in fields)
            if filled and accessibilite.cheminement_ext_presence is not True:
                accessibilite.cheminement_ext_presence = True
                accessibilite.save()
                print(f"Updated cheminement_ext_presence for {accessibilite.erp}.")
