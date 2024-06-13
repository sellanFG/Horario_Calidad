from django.shortcuts import render
from django.http import HttpResponse
from modulo_curso.models import escuela , plan_estudio, curso
from modulo_horario.models import grupo_horario, ciclo_academico

# Create your views here.
def Obtenercurso(plan):
    plan_es = plan_estudio.objects.filter(plan_nombre=plan)
    cursos = curso.objects.filter(FKplan_estudio__in = plan_es)
    return cursos


def obtenerGruposHorarios(id):
    grupos = grupo_horario.objects.filter(fk_curso_id=id)
    
    listado=[]
    for gh in grupos:
        listado.append(gh.grupo)

    return listado

def grupoHorario(request):
    escuelas = escuela.objects.all()
    escuela_select = request.POST.get('escuela')
    plan_select = request.POST.get('plan_estudio')
    curso_list = []
    listado=[]

    if escuela_select:
        escuela_se = escuela.objects.get(nombre_escuela=escuela_select)
        plan = plan_estudio.objects.filter(fk_escuela_id=escuela_se.id)

        if plan_select:
            plan_se = plan_estudio.objects.get(plan_nombre=plan_select)
            print(plan_se)
            cursos_plan = Obtenercurso(plan_se)

            for cur in cursos_plan:

                listado=obtenerGruposHorarios(cur.id)
                listado_sin_corchetes = ', '.join(listado)
                curso_list.append({
                    'id': cur.id,
                    'codigo_curso': cur.codigo_curso,
                    'ciclo_curso': cur.ciclo_curso,
                    'nombre_curso': cur.nombre_curso,
                    'grupos': listado_sin_corchetes
                })

            if request.method == 'POST':
                for cur in curso_list:
                    if request.POST.get('seleccionado_' + str(cur['id'])):
                        cantidad = int(request.POST.get('cantidad_' + str(cur['id'])))
                        for i in range(cantidad):
                            ciclo = ciclo_academico.objects.last()
                            curso_id = curso.objects.get(id=cur['id'])
                            ultimo_grupo = grupo_horario.objects.filter(fk_curso=curso_id).order_by('-grupo').first()
                            if ultimo_grupo:
                                nuevo_nombre = chr(ord(ultimo_grupo.grupo) + 1)
                            else:
                                nuevo_nombre = 'A'
                            grupo_horario.objects.create(grupo=nuevo_nombre, fk_curso=curso_id,fk_ciclo=ciclo)

            data = {
                'escuela' : escuelas,
                'escuela_select' : escuela_select,
                'plan_estudio' : plan,
                'plan_select' : plan_se.plan_nombre,
                'cursos' : curso_list
            }
            return render(request, 'grupoHorario.html', data)
        else:
            data = {
                'escuela' : escuelas,
                'escuela_select' : escuela_select,
                'plan_estudio' : plan,
            }
            return render(request, 'grupoHorario.html', data)
    else:
        data = {
            'escuela' : escuelas,
        }
        return render(request, 'grupoHorario.html', data)
    
