# Generated by Django 3.2.9 on 2022-08-03 21:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AMCE', '0010_rename_definirprob_fuentes_id_fuente_id_defproblema'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipo',
            name='paso',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='fuente',
            name='ganadora',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='fuente',
            name='votos',
            field=models.IntegerField(default=0),
        ),
    ]