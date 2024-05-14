from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# Create your views here.

def saludo(request):
    return render(request,'index.html')

def horario(request):
    return HttpResponse("horarios de los docentes")