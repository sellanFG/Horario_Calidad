# Generated by Django 5.0.6 on 2024-05-28 17:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_horario', '0003_grupo_horario'),
    ]

    operations = [
        migrations.AddField(
            model_name='horario',
            name='fk_grupo_horario',
            field=models.ForeignKey(blank=True, default=0, on_delete=django.db.models.deletion.CASCADE, to='modulo_horario.grupo_horario', verbose_name='Curso'),
            preserve_default=False,
        ),
    ]
