# Generated by Django 3.2.9 on 2022-08-04 01:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('AMCE', '0011_auto_20220803_1639'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comentariospreguntainicial',
            name='participacionEst',
        ),
        migrations.RemoveField(
            model_name='comentariospreguntainicial',
            name='pregunta',
        ),
        migrations.AddField(
            model_name='comentariospreguntainicial',
            name='comentario',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='comentariospreguntainicial',
            name='id_defproblema',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='definirproblemaEvFuente', to='AMCE.definirproblema'),
        ),
        migrations.AddField(
            model_name='comentariospreguntainicial',
            name='id_estudiante',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='estudianteEvFuente', to='AMCE.estudiante'),
        ),
        migrations.AddField(
            model_name='comentariospreguntainicial',
            name='id_fuente',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='AMCE.fuente'),
        ),
    ]
