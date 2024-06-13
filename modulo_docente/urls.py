from django.urls import path
from . import views

urlpatterns = [
    path('docente/', views.docente),
    path('csv/', views.upload_file),
    path('asignacionCargaLectiva/', views.asignacionCargaLectiva, name='asignacionCargaLectiva'),
    path('disponibilidadDocente/', views.disponibilidadDocente),

]