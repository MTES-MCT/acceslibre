# Generated by Django 4.2.16 on 2024-10-31 14:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("erp", "0170_department"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExternalSource",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("acceslibre", "Base de données Acceslibre"),
                            ("acceo", "Acceo"),
                            ("admin", "Back-office"),
                            ("api", "API"),
                            ("entreprise_api", "API Entreprise (publique)"),
                            ("cconforme", "cconforme"),
                            ("gendarmerie", "Gendarmerie"),
                            ("lorient", "Lorient"),
                            ("nestenn", "Nestenn"),
                            ("opendatasoft", "API OpenDataSoft"),
                            ("public", "Saisie manuelle publique"),
                            ("public_erp", "API des établissements publics"),
                            ("sap", "Sortir À Paris"),
                            ("service_public", "Service Public"),
                            ("sirene", "API Sirene INSEE"),
                            ("tourisme-handicap", "Tourisme & Handicap"),
                            ("typeform", "Questionnaires Typeform"),
                            ("typeform_musee", "Questionnaires Typeform Musée"),
                            ("centres-vaccination", "Centres de vaccination"),
                            ("dell", "Dell"),
                            ("outscraper", "Outscraper"),
                            ("scrapfly", "Scrapfly"),
                            ("scrapfly2", "Scrapfly2"),
                            ("tally", "Tally"),
                            ("laposte", "La Poste"),
                        ],
                        default="public",
                        help_text="Nom de la source de données dont est issu cet ERP",
                        max_length=100,
                        null=True,
                        verbose_name="Source",
                    ),
                ),
                (
                    "source_id",
                    models.CharField(help_text="Identifiant externe de cet ERP", max_length=64),
                ),
                (
                    "erp",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="erp.erp",
                        verbose_name="Établissement",
                    ),
                ),
            ],
        ),
    ]