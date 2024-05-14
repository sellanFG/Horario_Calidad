from django.urls import path
from . import views

urlpatterns = [
    path('docente/', views.docente),
    path('csv/', views.upload_file),
]