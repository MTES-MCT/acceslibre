import uuid

from django.conf import settings
from django.db import migrations, models

import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("erp", "0191_remove_accessibilite_erp_accessibilite_sanitaires_presence_consistency_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ErpTransferRequest",
            fields=[
                (
                    "id",
                    models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("accepted", "Accepté"),
                            ("refused", "Refusé"),
                            ("expired", "Expiré"),
                        ],
                        default="pending",
                        max_length=32,
                        verbose_name="Statut",
                    ),
                ),
                (
                    "token",
                    models.CharField(default=uuid.uuid4, max_length=64, unique=True, verbose_name="Jeton"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Date de la demande"),
                ),
                (
                    "responded_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="Date de réponse"),
                ),
                (
                    "reminder_sent_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="Date de la relance"),
                ),
                (
                    "erp",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transfer_requests",
                        to="erp.erp",
                        verbose_name="Établissement",
                    ),
                ),
                (
                    "new_manager",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Nouveau gestionnaire",
                    ),
                ),
                (
                    "previous_manager",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Gestionnaire actuel",
                    ),
                ),
            ],
            options={
                "verbose_name": "Demande de changement de gestionnaire",
                "verbose_name_plural": "Demandes de changement de gestionnaire",
            },
        ),
    ]
