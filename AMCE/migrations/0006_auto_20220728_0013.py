# Generated by Django 3.2.9 on 2022-07-28 05:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AMCE', '0005_fuente_definirprob_fuentes'),
    ]

    operations = [
        migrations.RenameField(
            model_name='fuente',
            old_name='definirProb_fuentes',
            new_name='definirProb_fuentes_id',
        ),
        migrations.AlterField(
            model_name='fuente',
            name='fecha_publicacion',
            field=models.DateField(null=True),
        ),
    ]
