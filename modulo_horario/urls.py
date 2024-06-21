from django.urls import path
from . import views
from modulo_ambiente import *
from modulo_usuario.views import *

urlpatterns = [
    path('inicio/', views.inicio),
    path('horario/', views.horariogestionar),
    path('inicio/menuHorario/', views.menuHorario,  name="menu_horario"),
    path('inicio/menuCurso/', views.menuCurso,  name="menu_curso"),
    path('inicio/menuDocente/', views.menuDocente,  name="menu_docente"),
    path('inicio/menuAmbiente/', views.menuAmbiente,  name="menu_ambiente"),
    path('asignacion_docente/', views.asignacion_docente, name="asignacion_docente"),
    path('horarioPorDocente/',views.horarioDocente),
    path('horarioPorCiclo/',views.horarioXCiclo),
]