# Generated by Django 4.2.11 on 2024-04-25 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("erp", "0164_erp_checked_up_to_date_at"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("transport_station_presence", True),
                        ("transport_station_presence__isnull", False),
                    ),
                    ("transport_information", ""),
                    ("transport_information__isnull", True),
                    _connector="OR",
                ),
                name="erp_accessibilite_transport_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("stationnement_presence", True),
                        ("stationnement_presence__isnull", False),
                    ),
                    ("stationnement_pmr", None),
                    _connector="OR",
                ),
                name="erp_accessibilite_stationnement_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("stationnement_ext_presence", True),
                        ("stationnement_ext_presence__isnull", False),
                    ),
                    ("stationnement_ext_pmr", None),
                    _connector="OR",
                ),
                name="erp_accessibilite_stationnement_ext_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("cheminement_ext_plain_pied", False),
                        ("cheminement_ext_plain_pied__isnull", False),
                    ),
                    models.Q(
                        ("cheminement_ext_ascenseur", None),
                        ("cheminement_ext_nombre_marches__isnull", True),
                        ("cheminement_ext_sens_marches__isnull", True),
                        ("cheminement_ext_reperage_marches__isnull", True),
                        ("cheminement_ext_main_courante__isnull", True),
                        ("cheminement_ext_rampe__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="erp_accessibilite_cheminement_ext_plain_pied_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("cheminement_ext_pente_presence", True),
                        ("cheminement_ext_pente_presence__isnull", False),
                    ),
                    models.Q(
                        ("cheminement_ext_pente_degre_difficulte__isnull", True),
                        ("cheminement_ext_pente_longueur__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="erp_accessibilite_cheminement_ext_pente_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("cheminement_ext_presence", True),
                        ("cheminement_ext_presence__isnull", False),
                    ),
                    models.Q(
                        ("cheminement_ext_terrain_stable__isnull", True),
                        ("cheminement_ext_plain_pied__isnull", True),
                        ("cheminement_ext_pente_presence__isnull", True),
                        ("cheminement_ext_devers__isnull", True),
                        ("cheminement_ext_bande_guidage__isnull", True),
                        ("cheminement_ext_retrecissement__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="erp_accessibilite_cheminement_ext_presence_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("entree_vitree", True), ("entree_vitree__isnull", False)),
                    ("entree_vitree_vitrophanie__isnull", True),
                    _connector="OR",
                ),
                name="erp_accessibilite_entree_vitree_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("entree_porte_presence", True),
                        ("entree_porte_presence__isnull", False),
                    ),
                    models.Q(
                        ("entree_porte_manoeuvre__isnull", True),
                        ("entree_porte_type__isnull", True),
                        ("entree_vitree__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="erp_accessibilite_entree_porte_presence_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("entree_plain_pied", False),
                        ("entree_plain_pied__isnull", False),
                    ),
                    models.Q(
                        ("entree_ascenseur__isnull", True),
                        models.Q(
                            ("entree_marches__isnull", True),
                            ("entree_marches", 0),
                            _connector="OR",
                        ),
                        ("entree_marches_sens__isnull", True),
                        ("entree_marches_reperage__isnull", True),
                        ("entree_marches_main_courante__isnull", True),
                        ("entree_marches_rampe__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="erp_accessibilite_entree_plain_pied_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("entree_dispositif_appel", True),
                        ("entree_dispositif_appel__isnull", False),
                    ),
                    ("entree_dispositif_appel_type__isnull", True),
                    ("entree_dispositif_appel_type", []),
                    _connector="OR",
                ),
                name="erp_accessibilite_entree_dispositif_appel_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("entree_pmr", True), ("entree_pmr__isnull", False)),
                    ("entree_pmr_informations__isnull", True),
                    ("entree_pmr_informations", ""),
                    _connector="OR",
                ),
                name="erp_accessibilite_entree_pmr_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("accueil_cheminement_plain_pied", True), _negated=True),
                    models.Q(
                        ("accueil_cheminement_ascenseur__isnull", True),
                        ("accueil_cheminement_nombre_marches__isnull", True),
                        ("accueil_cheminement_sens_marches__isnull", True),
                        ("accueil_cheminement_reperage_marches__isnull", True),
                        ("accueil_cheminement_main_courante__isnull", True),
                        ("accueil_cheminement_rampe__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="erp_accessibilite_accueil_cheminement_plain_pied_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("accueil_audiodescription_presence", True),
                        ("accueil_audiodescription_presence__isnull", False),
                    ),
                    ("accueil_audiodescription__isnull", True),
                    ("accueil_audiodescription", []),
                    _connector="OR",
                ),
                name="erp_accessibilite_accueil_audiodescription_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("accueil_equipements_malentendants_presence", True),
                        ("accueil_equipements_malentendants_presence__isnull", False),
                    ),
                    ("accueil_equipements_malentendants__isnull", True),
                    ("accueil_equipements_malentendants", []),
                    _connector="OR",
                ),
                name="erp_accessibilite_accueil_equipements_malentendants_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("sanitaires_presence", True),
                        ("sanitaires_presence__isnull", False),
                    ),
                    ("sanitaires_adaptes", None),
                    _connector="OR",
                ),
                name="erp_accessibilite_sanitaires_presence_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("labels", []),
                        ("labels__isnull", True),
                        _connector="OR",
                        _negated=True,
                    ),
                    models.Q(
                        models.Q(
                            ("labels_familles_handicap", []),
                            ("labels_familles_handicap__isnull", True),
                            _connector="OR",
                        ),
                        models.Q(
                            ("labels_autre__isnull", True),
                            ("labels_autre", ""),
                            _connector="OR",
                        ),
                    ),
                    _connector="OR",
                ),
                name="erp_accessibilite_labels_consistency",
            ),
        ),
        migrations.AddConstraint(
            model_name="accessibilite",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("accueil_chambre_nombre_accessibles", 0),
                        ("accueil_chambre_nombre_accessibles__isnull", True),
                        _connector="OR",
                        _negated=True,
                    ),
                    models.Q(
                        ("accueil_chambre_douche_plain_pied__isnull", True),
                        ("accueil_chambre_douche_siege__isnull", True),
                        ("accueil_chambre_douche_barre_appui__isnull", True),
                        ("accueil_chambre_sanitaires_barre_appui__isnull", True),
                        ("accueil_chambre_sanitaires_espace_usage__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="erp_accessibilite_chambre_consistency",
            ),
        ),
    ]
