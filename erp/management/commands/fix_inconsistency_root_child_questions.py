from django.core.management.base import BaseCommand
from django.db.models import Q

from erp.management.utils import print_error, print_success, print_warning
from erp.models import Accessibilite

PRINT_EXAMPLE = True


class Command(BaseCommand):
    def print_example(self, qs):
        if not PRINT_EXAMPLE:
            return

        published = qs.filter(erp__published=True)
        for access in published[0:2]:
            print_warning(f" Example: {access.erp.get_absolute_uri()}")

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--write",
            action="store_true",
            help="Actually edit the database",
        )

    def handle(self, *args, **options):
        write = options.get("write") or False

        print_warning("Root access fields")
        qs = Accessibilite.objects.filter(
            transport_station_presence__in=[None, False], transport_information__isnull=False
        ).exclude(transport_information="")
        print_error(f"Found {qs.count()} ERPs with inconsistent info on transport and its sub answers")
        self.print_example(qs)
        if write:
            qs.update(transport_information="")
            print_success("Fixed")

        qs = Accessibilite.objects.filter(
            ~(Q(stationnement_presence=True) | Q(stationnement_presence__isnull=False)), ~Q(stationnement_pmr=None)
        )
        print_error(f"Found {qs.count()} ERPs with inconsistent info on stationnement and its sub answers")
        self.print_example(qs)
        if write:
            qs.update(stationnement_pmr=None)
            print_success("Fixed")

        qs = Accessibilite.objects.filter(
            ~(Q(stationnement_ext_presence=True) | Q(stationnement_ext_presence__isnull=False)),
            ~Q(stationnement_ext_pmr=None),
        )
        print_error(f"Found {qs.count()} ERPs with inconsistent info on stationnement_ext and its sub answers")
        self.print_example(qs)
        if write:
            qs.update(stationnement_ext_presence=True)
            print_success("Fixed")

        qs = Accessibilite.objects.filter(
            (
                Q(cheminement_ext_plain_pied=None)
                | Q(cheminement_ext_plain_pied__isnull=True)
                | Q(cheminement_ext_plain_pied=True)
            )
            & (
                Q(cheminement_ext_ascenseur__isnull=False)
                | Q(cheminement_ext_nombre_marches__isnull=False)
                | Q(cheminement_ext_sens_marches__isnull=False)
                | Q(cheminement_ext_reperage_marches__isnull=False)
                | Q(cheminement_ext_main_courante__isnull=False)
                | Q(cheminement_ext_rampe__isnull=False)
            )
        )
        print_error(f"Found {qs.count()} ERPs with inconsistent info on cheminement_ext_plain_pied and its sub answers")
        self.print_example(qs)
        if write:
            qs.update(
                cheminement_ext_ascenseur=None,
                cheminement_ext_nombre_marches=None,
                cheminement_ext_sens_marches=None,
                cheminement_ext_reperage_marches=None,
                cheminement_ext_main_courante=None,
                cheminement_ext_rampe=None,
            )
            print_success("Fixed")

        qs = Accessibilite.objects.filter(
            Q(cheminement_ext_pente_presence=None)
            | Q(cheminement_ext_pente_presence__isnull=True)
            | Q(cheminement_ext_pente_presence=False)
        ).filter(
            ~Q(cheminement_ext_pente_degre_difficulte__isnull=True) | ~Q(cheminement_ext_pente_longueur__isnull=True)
        )

        print_error(
            f"Found {qs.count()} ERPs with inconsistent info on cheminement_ext_pente_presence and its sub answers"
        )
        self.print_example(qs)
        if write:
            qs.update(
                cheminement_ext_pente_degre_difficulte=None,
                cheminement_ext_pente_longueur=None,
            )
            print_success("Fixed")

        qs = Accessibilite.objects.filter(
            Q(Q(cheminement_ext_presence=None) | Q(cheminement_ext_presence=False))
            & (
                Q(cheminement_ext_terrain_stable__isnull=False)
                | Q(cheminement_ext_plain_pied__isnull=False)
                | Q(cheminement_ext_pente_presence__isnull=False)
                | Q(cheminement_ext_devers__isnull=False)
                | Q(cheminement_ext_bande_guidage__isnull=False)
                | Q(cheminement_ext_retrecissement__isnull=False)
            )
        )
        print_error(f"Found {qs.count()} ERPs with inconsistent info on cheminement_ext_presence and its sub answers")
        self.print_example(qs)
        if write:
            qs.update(cheminement_ext_presence=True)
            print_success("Fixed")

        qs = Accessibilite.objects.filter(
            Q(Q(entree_vitree=None) | Q(entree_vitree=False)), entree_vitree_vitrophanie__isnull=False
        )
        print_error(f"Found {qs.count()} ERPs with inconsistent info on entree_vitree and its sub answers")
        self.print_example(qs)
        if write:
            qs.update(entree_vitree=True)
            print_success("Fixed")

        qs = Accessibilite.objects.filter(
            Q(Q(entree_porte_presence=None) | Q(entree_porte_presence=False))
            & (
                Q(entree_porte_manoeuvre__isnull=False)
                | Q(entree_porte_type__isnull=False)
                | Q(entree_vitree__in=[True, False])
            )
        )
        print_error(f"Found {qs.count()} ERPs with inconsistent info on entree_porte_presence and its sub answers")
        self.print_example(qs)
        if write:
            qs.update(entree_porte_presence=True)
            print_success("Fixed")

        qs = Accessibilite.objects.filter(
            Q(Q(entree_plain_pied=None) | Q(entree_plain_pied=True))
            & (
                Q(entree_ascenseur__in=[True, False])
                | Q(entree_marches__isnull=False)
                | Q(entree_marches_sens__isnull=False)
                | Q(entree_marches_reperage__in=[True, False])
                | Q(entree_marches_main_courante__in=[True, False])
                | Q(entree_marches_rampe__isnull=False)
            )
        )
        print_error(f"Found {qs.count()} ERPs with inconsistent info on entree_plain_pied and its sub answers")
        self.print_example(qs)
        if write:
            qs.update(entree_plain_pied=False)
            print_success("Fixed")

        qs = Accessibilite.objects.filter(Q(entree_dispositif_appel=None) | Q(entree_dispositif_appel=False)).exclude(
            Q(entree_dispositif_appel_type=[]) | Q(entree_dispositif_appel_type=None)
        )
        print_error(f"Found {qs.count()} ERPs with inconsistent info on entree_dispositif_appel and its sub answers")
        self.print_example(qs)
        if write:
            qs.update(entree_dispositif_appel_type=None)
            print_success("Fixed")

        qs = Accessibilite.objects.filter(entree_pmr__in=[None, False]).exclude(entree_pmr_informations="")
        print_error(f"Found {qs.count()} ERPs with inconsistent info on entree_pmr and its sub answers")
        self.print_example(qs)

        if write:
            qs.update(entree_pmr_informations="")
            print_success("Fixed")

        qs = Accessibilite.objects.filter(
            Q(Q(accueil_cheminement_plain_pied=None) | Q(accueil_cheminement_plain_pied=True))
            & (
                Q(accueil_cheminement_ascenseur__in=[True, False])
                | Q(accueil_cheminement_nombre_marches__isnull=False)
                | Q(accueil_cheminement_sens_marches__isnull=False)
                | Q(accueil_cheminement_reperage_marches__in=[True, False])
                | Q(accueil_cheminement_main_courante__in=[True, False])
                | Q(accueil_cheminement_rampe__isnull=False)
            )
        )
        print_error(
            f"Found {qs.count()} ERPs with inconsistent info on accueil_cheminement_plain_pied and its sub answers"
        )
        self.print_example(qs)
        if write:
            qs.update(
                accueil_cheminement_ascenseur=None,
                accueil_cheminement_nombre_marches=None,
                accueil_cheminement_sens_marches=None,
                accueil_cheminement_reperage_marches=None,
                accueil_cheminement_main_courante=None,
                accueil_cheminement_rampe=None,
            )
            print_success("Fixed")

        qs = (
            Accessibilite.objects.filter(accueil_audiodescription_presence__in=[None, False])
            .exclude(accueil_audiodescription=None)
            .exclude(accueil_audiodescription=[])
        )
        print_error(f"Found {qs.count()} ERPs with inconsistent info on accueil_audio_description and its sub answers")
        self.print_example(qs)
        if write:
            qs.update(accueil_audiodescription=None)
            print_success("Fixed")

        qs = (
            Accessibilite.objects.filter(accueil_equipements_malentendants_presence__in=[None, False])
            .exclude(accueil_equipements_malentendants=None)
            .exclude(accueil_equipements_malentendants=[])
        )
        print_error(
            f"Found {qs.count()} ERPs with inconsistent info on accueil_equipements_malentendants and its sub answers"
        )
        self.print_example(qs)
        if write:
            qs.update(accueil_equipements_malentendants=None)
            print_success("Fixed")

        qs = Accessibilite.objects.filter(
            Q(Q(sanitaires_presence=None) | Q(sanitaires_presence=False)), sanitaires_adaptes__in=[True, False]
        )
        print_error(f"Found {qs.count()} ERPs with inconsistent info on sanitaires_presence and its sub answers")
        self.print_example(qs)
        if write:
            qs.update(sanitaires_adaptes=None)
            print_success("Fixed")

        qs = Accessibilite.objects.filter(labels=[]).filter(
            ~Q(labels_familles_handicap=[]) | ~Q(labels_autre__isnull=True)
        )
        print_error(f"Found {qs.count()} ERPs with inconsistent info on labels and its sub answers")
        self.print_example(qs)
        if write:
            qs.update(labels_familles_handicap=[], labels_autre=None)
            print_success("Fixed")

        print_warning("Conditional questions")

        qs = Accessibilite.objects.filter(
            Q(Q(accueil_chambre_nombre_accessibles__lte=0) | Q(accueil_chambre_nombre_accessibles=None))
            & (
                Q(accueil_chambre_douche_plain_pied__in=[True, False])
                | Q(accueil_chambre_douche_siege__in=[True, False])
                | Q(accueil_chambre_douche_barre_appui__in=[True, False])
                | Q(accueil_chambre_sanitaires_barre_appui__in=[True, False])
                | Q(accueil_chambre_sanitaires_espace_usage__in=[True, False])
                | Q(accueil_chambre_equipement_alerte__isnull=False)
                | Q(accueil_chambre_numero_visible__isnull=False)
                | Q(accueil_chambre_sanitaires_espace_usage__isnull=False)
                | Q(accueil_chambre_accompagnement__isnull=False)
            )
        )
        print_error(
            f"Found {qs.count()} ERPs with inconsistent info on accueil_chambre_nombre_accessibles and its sub answers"
        )
        self.print_example(qs)
        if write:
            qs.update(accueil_chambre_nombre_accessibles=1)
            print_success("Fixed")
