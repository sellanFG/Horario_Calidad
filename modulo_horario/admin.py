from django.contrib import admin
from .models import horario, dia_semana, ciclo_academico

# Register your models here.
admin.site.register(horario)
admin.site.register(dia_semana)
admin.site.register(ciclo_academico)
