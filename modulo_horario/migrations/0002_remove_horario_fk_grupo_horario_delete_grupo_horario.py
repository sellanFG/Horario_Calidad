# Generated by Django 5.0.6 on 2024-05-28 17:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('modulo_horario', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='horario',
            name='fk_grupo_horario',
        ),
        migrations.DeleteModel(
            name='grupo_horario',
        ),
    ]
