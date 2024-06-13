from pyexpat import model
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from datetime import date, datetime, timedelta
from modulo_curso.models import escuela , plan_estudio, curso
from modulo_horario.models import escuela_ambiente, grupo_horario,dia_semana,horario,escuela_ambiente
from modulo_docente.models import disponibilidad_docente, docente, docente_grupo
from modulo_ambiente.models import ambiente
from pulp import LpMinimize, LpProblem, LpVariable, lpSum
from ortools.sat.python import cp_model

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
    return HttpResponse("Gestionar horario")


def login(request):
    return render(request,'Login.html')


def asignacion_docente(request):

    if request.method == 'POST':

        # Datos de entrada para la asignación
        # Ambientes asignados a la escuela
        ids_ambiente_de_escuela = escuela_ambiente.objects.values_list('FK_ambiente_id', flat=True).distinct()

        ambientes = ambiente.objects.filter(id__in=ids_ambiente_de_escuela, estado_ambiente='D')
        

        # Obtener una lista de objetos grupo_horario
        grupos_horario = list(grupo_horario.objects.all())
        
        # Inicializar el diccionario grupos con claves que sean los id de cada grupo_horario
        grupos = {grupo.id: {} for grupo in grupos_horario}
        
        # Iterar sobre los objetos grupo_horario obtenidos
        for grupo in grupos_horario:
            # Obtener el objeto curso asociado
            curso_del_grupo = grupo.fk_curso
            
            # Extraer la información relevante del curso
            horas_totales = curso_del_grupo.horas_totales
            ciclo = curso_del_grupo.ciclo_curso
            ambiente_preferido = curso_del_grupo.amb  # Asumiendo que 'amb' es el ambiente preferido
            
            # Crear o actualizar un diccionario para el grupo_horario actual en grupos
            grupos[grupo.id]['nombre_grupo'] = grupo.grupo
            grupos[grupo.id]['nombre_curso'] = curso_del_grupo.nombre_curso
            grupos[grupo.id]['horas_totales'] = horas_totales
            grupos[grupo.id]['ciclo'] = ciclo
            grupos[grupo.id]['ambiente_preferido'] = ambiente_preferido
            
            # Obtener y asignar la lista de docentes asociados al grupo actual
            grupos[grupo.id]['docentes'] = list(docente_grupo.objects.filter(FKgrupo=grupo).values_list('id', flat=True))

        # Docentes que aparecen en los grupos (ya asignados)
        ids_docente = docente_grupo.objects.values_list('FKdocente_id', flat=True).distinct()

        docentes = docente.objects.filter(id__in=ids_docente)

        # Disponibilidades de los docentes que están ya asignados
        disponibilidad_docen = disponibilidad_docente.objects.filter(FKdocente_id__in=ids_docente)
        disponibilidades = []

        for disponibilidad in disponibilidad_docen:
            hora_inicio = disponibilidad.ddo_horainicio.hour  # Extraer la hora de inicio como entero
            hora_fin = disponibilidad.ddo_horafin.hour       # Extraer la hora de fin como entero
            dif_horas = abs(hora_fin - hora_inicio)

            for i in range(dif_horas):
                obj_disp = disponibilidad_docente()
                obj_disp.FKdocente_id = disponibilidad.FKdocente_id
                obj_disp.ddo_horainicio = hora_inicio + i # Asignar la hora de inicio actual
                obj_disp.ddo_horafin = hora_inicio + i + 1  # Asignar la hora de fin actual
                obj_disp.FKdiasemana_id = disponibilidad.FKdiasemana_id
                disponibilidades.append(obj_disp)

        # Días 
        dias = dia_semana.objects.all()
        horas = [7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22]

        problema = cp_model.CpModel()
        # Crear variables horario donde se asignará el horario de cada docente
        horario_vars = {}
        ##start_time = tiempo.time()

        for grupo_id, grupo_data in grupos.items():
            for ambien in ambientes:
                for dia in dias:
                    for hora_inicio in (horas):
                        clave = (grupo_id, ambien.nombre_ambiente, dia.dia_nombre, hora_inicio, hora_inicio + 1)
                        horario_vars[clave] = problema.NewBoolVar(f'horario_{clave}')


        # Restricción para generar solo las horas necesarias según horas teóricas y prácticas

        for grupo_id, grupo_data in grupos.items():
            vars_horario_grupo = []
            for dia in dias:
                for hora_inicio in horas:
                    for ambien in ambientes:
                        clave = (grupo_id, ambien.nombre_ambiente, dia.dia_nombre, hora_inicio, hora_inicio + 1)
                        vars_horario_grupo.append(horario_vars[clave])
            problema.Add(sum(vars_horario_grupo) == grupo_data['horas_totales'])
        

        # Restricción de disponibilidad de los docentes

        for docen in docentes:
            for grupo_id, grupo_data in grupos.items():  # Iterar sobre claves y valores del diccionario
                docentes_del_grupo = docente_grupo.objects.filter(FKgrupo_id=grupo_id).values_list('FKdocente_id', flat=True)  # Obtener IDs de docentes del grupo
                if docen.id in docentes_del_grupo:  # Verificar si el docente está en el grupo
                    disponibilidades_docente = [disp for disp in disponibilidades if disp.FKdocente_id == docen.id]
                    for ambien in ambientes:
                        for dia in dias:
                            for hora_inicio in horas:
                                clave = (grupo_id, ambien.nombre_ambiente, dia.dia_nombre, hora_inicio, hora_inicio + 1)
                                if clave in horario_vars:
                                    disponibilidad = next((disp for disp in disponibilidades_docente if disp.FKdiasemana_id == dia.id and hora_inicio >= disp.ddo_horainicio and hora_inicio < disp.ddo_horafin), None)
                                    if not disponibilidad:
                                        problema.Add(horario_vars[clave] == 0)
                            
        # Restriccion para que no se crucen los docentes
        for docen in docentes:
            for dia in dias:
                for hora_inicio in horas:
                    restriccion_docente = []
                    for grupo_id, grupo_data in grupos.items():
                        docentes_del_grupo = docente_grupo.objects.filter(FKgrupo_id=grupo_id).values_list('FKdocente_id', flat=True)
                        if docen.id in docentes_del_grupo:
                            for ambien in ambientes:
                                clave = (grupo_id, ambien.nombre_ambiente, dia.dia_nombre, hora_inicio, hora_inicio + 1)
                                if clave in horario_vars:
                                    restriccion_docente.append(horario_vars[clave])

                    problema.Add(sum(restriccion_docente) <= 1)


        # Restricción de disponibilidad de ambiente

        for dia in dias:
            for hora_inicio in horas:
                for ambien in ambientes:
                    vars_horario_ambiente = []
                    for grupo_id, grupo_data in grupos.items():
                        clave = (grupo_id, ambien.nombre_ambiente, dia.dia_nombre, hora_inicio, hora_inicio + 1)
                        vars_horario_ambiente.append(horario_vars[clave])
                        
                    problema.Add(sum(vars_horario_ambiente) <= 1)

        # # Restricción de ambiente preferido
        # #start_time = tiempo.time()

        # for grupo_id, grupo_data in grupos.items():
        #     for ambien in ambientes:
        #         for dia in dias:
        #             for hora_inicio in horas:
        #                 if grupo_data['ambiente_preferido'] != ambien.FKtipo_ambiente:
        #                     clave = (grupo_data['nombre_grupo'], ambien.nombre_ambiente, dia.dia_nombre, hora_inicio, hora_inicio + 1)
        #                     problema.Add(horario_vars[clave] == 0)

        # # Restricción de ciclos preferidos
        # horas_manana = [hora for hora in horas if hora < 12]
        # horas_tarde = [hora for hora in horas if hora >= 12]

        # Restricción adicional: no más de 3 horas de clase de un grupo por día
        #start_time = tiempo.time()

        for grupo_id, grupo_data in grupos.items():
            for dia in dias:
                for ambien in ambientes:
                    vars_horario_grupo_dia = []
                    for hora_inicio in horas:
                        clave = (grupo_id, ambien.nombre_ambiente, dia.dia_nombre, hora_inicio, hora_inicio + 1)
                        vars_horario_grupo_dia.append(horario_vars[clave])
                
                    tiene_clases = problema.NewBoolVar(f'tiene_clases_{grupo.id}_{dia.dia_nombre}')
                    problema.Add(sum(vars_horario_grupo_dia) >= 2).OnlyEnforceIf(tiene_clases)
                    problema.Add(sum(vars_horario_grupo_dia) <= 3).OnlyEnforceIf(tiene_clases)
                    problema.Add(sum(vars_horario_grupo_dia) == 0).OnlyEnforceIf(tiene_clases.Not())

        #Restricción para generar horarios de grupo juntos
        costo_huecos = 0
        for grupo_id, grupo_data in grupos.items():
            for ambien in ambientes:
                for dia in dias:
                    for i in range(len(horas) - 1):
                        hora_inicio1 = horas[i]
                        hora_inicio2 = horas[i + 1]
                        clave1 = (grupo_id, ambien.nombre_ambiente, dia.dia_nombre, hora_inicio1, hora_inicio1 + 1)
                        clave2 = (grupo_id, ambien.nombre_ambiente, dia.dia_nombre, hora_inicio2, hora_inicio2 + 1)
                        
                        # Variable para el costo del hueco
                        costo_hueco = problema.NewIntVar(0, hora_inicio2 - hora_inicio1 - 1, f'costo_hueco_{grupo_id}{ambien.nombre_ambiente}{dia.dia_nombre}{hora_inicio1}{hora_inicio2}')

                        # Restricciones para calcular el costo del hueco
                        problema.Add(costo_hueco == 0).OnlyEnforceIf([horario_vars[clave1], horario_vars[clave2]])  # Ambas clases programadas
                        problema.Add(costo_hueco == hora_inicio2 - hora_inicio1 - 1).OnlyEnforceIf([horario_vars[clave1].Not(), horario_vars[clave2].Not()])  # Ninguna clase programada
                        problema.Add(costo_hueco == 0).OnlyEnforceIf([horario_vars[clave1], horario_vars[clave2].Not()])  # Solo la primera clase programada
                        problema.Add(costo_hueco == 0).OnlyEnforceIf([horario_vars[clave1].Not(), horario_vars[clave2]])  # Solo la segunda clase programada

                        # Acumular el costo
                        costo_huecos += costo_hueco

        # Minimizar directamente el costo total
        problema.Minimize(costo_huecos)

        #Restriccion para que no se crucen horarios del mismo grupo y denominacion

        vars_por_denominacion = {}
        denominaciones=[]
        ciclos=[]
        for grupo_id, grupo_data in grupos.items():
            denominaciones.append(grupo_data['nombre_grupo'])
            ciclos.append(grupo_data['ciclo'])
        denominaciones = list(set(denominaciones))
        ciclos = list(set(ciclos))

        for dia in dias:
                for hora_inicio in horas:
                    for denominacion in denominaciones:
                        for ciclo in ciclos:
                            vars_por_denominacion[(denominacion, ciclo, dia.dia_nombre, hora_inicio)] = []

        for ambien in ambientes:
            for dia in dias:
                for hora_inicio in horas:
                    for grupo_id, grupo_data in grupos.items():
                        clave = (grupo_id, ambien.nombre_ambiente, dia.dia_nombre, hora_inicio, hora_inicio + 1)
                        # Agregar la variable de horario al grupo correspondiente
                        vars_por_denominacion[(grupo_data['nombre_grupo'], grupo_data['ciclo'], dia.dia_nombre, hora_inicio)].append(horario_vars[clave])



        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 80000
        status = solver.Solve(problema)

        horarios_finales = []

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print("Solución encontrada")

            for grupo_id, grupo_data in grupos.items():
                for dia in dias:
                    for hora_inicio in horas:
                        for ambien in ambientes:
                            clave = (grupo_id, ambien.nombre_ambiente, dia.dia_nombre, hora_inicio, hora_inicio + 1)
                            if clave in horario_vars and solver.Value(horario_vars[clave]) == 1:
                                horarios_finales.append(clave)
                                cur = curso.objects.filter(id=grupo.fk_curso_id).first()
                                docentes_grupo = docente_grupo.objects.filter(FKgrupo_id=grupo_id).all()
                                docentes = [docente_grupo.FKdocente_id for docente_grupo in docentes_grupo]
                                print(f"Grupo {grupo_data['nombre_curso']}-{grupo_data['nombre_grupo']} asignado a Ambiente {ambien.nombre_ambiente} el Día {dia.dia_nombre} a las {hora_inicio}:00 con Docentes {docentes}")
        else:
            print("No se pudo encontrar una solución óptima o factible.")
            
        return render(request,'asignacion.html')
    else:
        
        if disponibilidad_docente.objects.exists():
            msjedispo="✔"
        else:
            msjedispo="✖"
        
        if escuela_ambiente.objects.exists():
            msjesc="✔"
        else:
            msjesc="✖"

        datos= {
            "d":msjedispo,
            "a":msjesc,
        }

        return render(request,'asignacion.html', datos)