from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# Create your views here.

def inicio(request):
    return render(request,'index.html')

def menuHorario(request):
    return render(request,'menuHorario.html')

def menuCurso(request):
    return render(request,'menuCurso.html')

def menuDocente(request):
    return render(request,'menuDocente.html')

def menuAmbiente(request):
    return render(request,'menuAmbiente.html')


def horario(request):
    return HttpResponse("horarios de los docentes")