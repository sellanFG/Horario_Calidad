from django.urls import path
from . import views

urlpatterns = [
    path('', views.saludo),
    path('horario/', views.horario),
    path('asignacion_docente/', views.asignacion_docente, name="asignacion_docente"),
    
]