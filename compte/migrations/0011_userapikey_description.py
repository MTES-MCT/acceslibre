from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("compte", "0010_auto_20260715_1512"),
    ]

    operations = [
        migrations.AddField(
            model_name="userapikey",
            name="description",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Besoin exprimé par l'utilisateur lors de la demande de clef d'API.",
                verbose_name="Description",
            ),
        ),
    ]
