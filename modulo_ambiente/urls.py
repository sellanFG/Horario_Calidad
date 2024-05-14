from django.urls import path
from . import views

urlpatterns = [
    path('ambiente/', views.ambiente)
]