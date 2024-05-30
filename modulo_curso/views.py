from django.shortcuts import render
from django.http import HttpResponse
from modulo_curso.models import escuela , plan_estudio, curso
# from modulo_horario.models import grupo_horario, ciclo_academico

# Create your views here.
def Obtenercurso(plan):
    plan_es = plan_estudio.objects.filter(plan_nombre=plan)
    cursos = curso.objects.filter(FKplan_estudio__in = plan_es)
    return cursos


# def grupoHorario(request):
#     escuelas = escuela.objects.all()
#     escuela_select = request.POST.get('escuela')
#     plan_select = request.POST.get('plan_estudio')
#     curso_list = []


#     if escuela_select:
#         escuela_se = escuela.objects.get(nombre_escuela=escuela_select)
#         plan = plan_estudio.objects.filter(fk_escuela_id=escuela_se.id)

#         if plan_select:
#             plan_se = plan_estudio.objects.get(plan_nombre=plan_select)
#             print(plan_se)
#             cursos_plan = Obtenercurso(plan_se)

#             for cur in cursos_plan:
#                 curso_list.append({
#                     'id': cur.id,
#                     'codigo_curso': cur.codigo_curso,
#                     'ciclo_curso': cur.ciclo_curso,
#                     'nombre_curso': cur.nombre_curso,
#                 })
#                 if request.method == 'POST':
#                     for cur in curso_list:
#                         if request.POST.get('seleccionado_' + str(cur['id'])):
#                             cantidad = int(request.POST.get('cantidad_' + str(cur['id'])))
#                             for i in range(cantidad):
#                                 ciclo = ciclo_academico.objects.last()
#                                 curso_id = curso.objects.get(id=cur['id'])
#                                 grupo_horario.objects.create(nombre_grupo=chr(65 + i), fk_curso=curso_id,fk_ciclo_academico=ciclo)

#             data = {
#                 'escuela' : escuelas,
#                 'escuela_select' : escuela_select,
#                 'plan_estudio' : plan,
#                 'plan_select' : plan_se.plan_nombre,
#                 'cursos' : curso_list
#             }
#             return render(request, 'grupoHorario.html', data)
#         else:
#             data = {
#                 'escuela' : escuelas,
#                 'escuela_select' : escuela_select,
#                 'plan_estudio' : plan,
#             }
#             return render(request, 'grupoHorario.html', data)
#     else:
#         data = {
#             'escuela' : escuelas,
#         }
#         return render(request, 'grupoHorario.html', data)
    
