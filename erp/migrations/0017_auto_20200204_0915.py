# Generated by Django 3.0.3 on 2020-02-04 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0016_auto_20200204_0843'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cheminement',
            name='devers',
            field=models.CharField(blank=True, choices=[('aucun', 'Aucun'), ('léger', 'Léger'), ('important', 'Important')], help_text='Présence et type de dévers', max_length=15, null=True, verbose_name='Dévers'),
        ),
        migrations.AlterField(
            model_name='cheminement',
            name='pente',
            field=models.CharField(blank=True, choices=[('aucune', 'Aucune'), ('légère', 'Légère'), ('importante', 'Importante')], help_text='Présence et type de pente', max_length=15, null=True),
        ),
    ]
