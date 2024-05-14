from django.contrib import admin
from .models import docente, disponibilidad_docente, departamento_academico, tipo_contrato

# Register your models here.
admin.site.register(docente)
admin.site.register(disponibilidad_docente)
admin.site.register(departamento_academico)
admin.site.register(tipo_contrato)
