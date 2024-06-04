from django.urls import path
from . import views
from modulo_ambiente import *
from modulo_usuario.views import *

urlpatterns = [
    path('inicio/', views.inicio),
    path('horario/', views.horario),
    path('menuHorario/', views.menuHorario),
    path('menuCurso/', views.menuCurso),
    path('menuDocente/', views.menuDocente),
    path('menuAmbiente/', views.menuAmbiente),
    path('asignacion_docente/', views.asignacion_docente, name="asignacion_docente"),
    
]