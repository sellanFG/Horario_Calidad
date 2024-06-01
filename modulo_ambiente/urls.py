from django.urls import path
from . import views

urlpatterns = [
    path('ambiente/', views.ambiente),
    path('asignarAmbiente/', views.asignarAmbiente),
    path('csvAmbientes/', views.upload_file)
]