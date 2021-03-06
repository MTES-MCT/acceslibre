# Generated by Django 3.0.3 on 2020-02-05 07:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0019_auto_20200204_0946'),
    ]

    operations = [
        migrations.CreateModel(
            name='EquipementMalentendant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(help_text="Nom de l'équipement", max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Dernière modification')),
            ],
            options={
                'verbose_name': 'Équipement sourd/malentendant',
                'verbose_name_plural': 'Équipements sourd/malentendant',
            },
        ),
        migrations.RemoveField(
            model_name='accessibilite',
            name='accueil_bim',
        ),
        migrations.RemoveField(
            model_name='accessibilite',
            name='accueil_lsf',
        ),
        migrations.RemoveField(
            model_name='accessibilite',
            name='accueil_sous_titrage',
        ),
        migrations.RemoveField(
            model_name='accessibilite',
            name='entree_secondaire',
        ),
        migrations.AddField(
            model_name='accessibilite',
            name='accueil_visibilite',
            field=models.BooleanField(blank=True, help_text="Visibilité de l'accueil depuis l'entrée", null=True, verbose_name="Visibilité de l'accueil"),
        ),
        migrations.AddField(
            model_name='accessibilite',
            name='entree_pmr',
            field=models.BooleanField(blank=True, help_text="Présence d'une entrée secondaire spécifique PMR", null=True, verbose_name='Entrée spécifique PMR'),
        ),
        migrations.AddField(
            model_name='accessibilite',
            name='stationnement_ext_pmr',
            field=models.BooleanField(blank=True, help_text='Présence de stationnements adaptés à proximité (200m)', null=True, verbose_name='Stationnements PMR à proximité'),
        ),
        migrations.AddField(
            model_name='accessibilite',
            name='stationnement_ext_presence',
            field=models.BooleanField(blank=True, help_text='Présence de stationnements à proximité (200m)', null=True, verbose_name='Stationnement à proximité'),
        ),
        migrations.AddField(
            model_name='erp',
            name='site_internet',
            field=models.CharField(blank=True, help_text="Adresse du site internet de l'ERP", max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='erp',
            name='telephone',
            field=models.CharField(blank=True, help_text="Numéro de téléphone de l'ERP", max_length=20, null=True, verbose_name='Téléphone'),
        ),
        migrations.AlterField(
            model_name='accessibilite',
            name='accueil_personnels',
            field=models.CharField(blank=True, choices=[('aucun', 'Aucun personnel'), ('formés', 'Personnels sensibilisés et formés'), ('non-formés', 'Personnels non non-formés')], help_text="Présence et type de personnels d'accueil", max_length=255, null=True, verbose_name="Personnel d'accueil"),
        ),
        migrations.AlterField(
            model_name='accessibilite',
            name='entree_secondaire_informations',
            field=models.TextField(blank=True, help_text="Précisions sur les modalités d'accès de l'entrée spécifique PMR", max_length=500, null=True, verbose_name='Infos entrée spécifique PMR'),
        ),
        migrations.AlterField(
            model_name='accessibilite',
            name='entree_signaletique',
            field=models.BooleanField(blank=True, help_text="Présence d'éléments de répérage matérialisant l'entrée", null=True, verbose_name="Éléments de repérage de l'entrée"),
        ),
        migrations.AlterField(
            model_name='accessibilite',
            name='labels',
            field=models.ManyToManyField(blank=True, help_text="Labels d'accessibilité obtenus par l'ERP (maintenez la touche Ctrl enfoncée pour sélectionner plusieurs entrées)", null=True, to='erp.Label'),
        ),
        migrations.AlterField(
            model_name='accessibilite',
            name='stationnement_pmr',
            field=models.BooleanField(blank=True, help_text="Présence de stationnements adaptés au sein de l'ERP", null=True, verbose_name="Stationnements PMR dans l'ERP"),
        ),
        migrations.AlterField(
            model_name='accessibilite',
            name='stationnement_presence',
            field=models.BooleanField(blank=True, help_text="Présence de stationnements au sein de l'ERP", null=True, verbose_name="Stationnement dans l'ERP"),
        ),
        migrations.AlterField(
            model_name='erp',
            name='code_insee',
            field=models.CharField(blank=True, help_text='Code INSEE', max_length=5, null=True),
        ),
        migrations.AlterField(
            model_name='erp',
            name='code_postal',
            field=models.CharField(help_text='Code postal', max_length=5),
        ),
        migrations.AlterField(
            model_name='erp',
            name='siret',
            field=models.CharField(blank=True, help_text="Numéro SIRET si l'ERP est une entreprise", max_length=14, null=True, verbose_name='SIRET'),
        ),
        migrations.AlterField(
            model_name='label',
            name='nom',
            field=models.CharField(help_text='Nom du label', max_length=255),
        ),
        migrations.AddField(
            model_name='accessibilite',
            name='accueil_equipements_malentendants',
            field=models.ManyToManyField(blank=True, help_text='Choix multiple possible (maintenez la touche Ctrl enfoncée pour sélectionner plusieurs entrées)', null=True, to='erp.EquipementMalentendant', verbose_name='Équipements sourds/malentendants'),
        ),
    ]
