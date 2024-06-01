from django.contrib import admin
from .models import edificio, tipo_ambiente, ambiente, horarioEscuela
# Register your models here.
admin.site.register(edificio)
admin.site.register(tipo_ambiente)
admin.site.register(ambiente)
admin.site.register(horarioEscuela)

admin.site.site_header="Administración del Sistema Generador de Horarios-USAT"
admin.site.site_title="Administración del Sistema Generador de Horarios-USAT"
admin.site.index_title=""


