# Generated by Django 5.0.6 on 2024-05-28 17:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_curso', '0011_curso_ciclo_curso'),
        ('modulo_horario', '0002_remove_horario_fk_grupo_horario_delete_grupo_horario'),
    ]

    operations = [
        migrations.CreateModel(
            name='grupo_horario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grupo', models.CharField(max_length=1)),
                ('fk_ciclo', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='modulo_horario.ciclo_academico')),
                ('fk_curso', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='modulo_curso.curso')),
            ],
            options={
                'verbose_name_plural': 'Grupo Horario',
            },
        ),
    ]
