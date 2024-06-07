from django.urls import path
from . import views
from modulo_ambiente import *
from modulo_usuario.views import *

urlpatterns = [
    path('inicio/', views.inicio),
    path('horario/', views.horario),
    path('inicio/menuHorario/', views.menuHorario),
    path('inicio/menuCurso/', views.menuCurso),
    path('inicio/menuDocente/', views.menuDocente),
    path('inicio/menuAmbiente/', views.menuAmbiente),
    path('asignacion_docente/', views.asignacion_docente, name="asignacion_docente"),
    
]