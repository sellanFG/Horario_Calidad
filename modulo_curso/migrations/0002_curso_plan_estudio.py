# Generated by Django 5.0.4 on 2024-04-12 21:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_curso', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='curso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cur_nombre', models.CharField(max_length=100)),
                ('cur_horassemana', models.SmallIntegerField()),
                ('cur_horastotales', models.SmallIntegerField()),
                ('cur_horaspracticas', models.SmallIntegerField()),
                ('cur_horasteoricas', models.SmallIntegerField()),
                ('cur_escuela', models.IntegerField(default=1)),
                ('cur_tipo', models.IntegerField(default=1)),
                ('cur_plan', models.IntegerField(default=1)),
                ('FKescuela', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='modulo_curso.escuela')),
                ('FKtipocurso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='modulo_curso.tipo_curso')),
            ],
        ),
        migrations.CreateModel(
            name='plan_estudio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_nombre', models.CharField(max_length=60)),
                ('plan_descripcion', models.CharField(max_length=60)),
                ('plan_fechacreacion', models.DateField()),
                ('plan_curso', models.IntegerField(default=1)),
                ('FKcurso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='modulo_curso.curso')),
            ],
        ),
    ]
