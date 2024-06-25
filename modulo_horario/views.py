from pyexpat import model
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect,get_object_or_404
from django.views.decorators.http import require_POST
from datetime import date, datetime, timedelta
from modulo_curso.models import escuela , plan_estudio, curso
from modulo_horario.models import escuela_ambiente, grupo_horario,dia_semana,horario,escuela_ambiente,horario, ciclo_academico
from modulo_docente.models import disponibilidad_docente, docente, docente_grupo
from modulo_ambiente.models import ambiente, edificio, tipo_ambiente
from pulp import LpMinimize, LpProblem, LpVariable, lpSum
from ortools.sat.python import cp_model
from datetime import datetime, time

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

def horariogestionar(request):
    return HttpResponse("Gestionar horario")


def login(request):
    return render(request,'Login.html')


def obtenerGruposHorariosDocentes(docente_seleccionado):
    enviar=[]
    docentes=[]
    
    gh = grupo_horario.objects.filter(fk_ciclo=1)
             
    for grupo_obj in gh:
                
                g_id = grupo_obj.id
                nombre = grupo_obj.fk_curso
                g_nombre = grupo_obj.grupo
                ghdocente= docente_grupo.objects.filter(FKgrupo=g_id)

                docentes = [ghdobj.FKdocente for ghdobj in ghdocente]

                if docente_seleccionado in docentes:
                    enviar.append((nombre, g_nombre, docente_seleccionado,g_id))
    
    return enviar


def horarioDocente(request):
    ids_docente = docente_grupo.objects.values_list('FKdocente_id', flat=True).distinct()
    docentes = docente.objects.filter(id__in=ids_docente)
    horario_final = None
    docente_id = None
    ghs=[]
    horario_final = []

    #! agregado
    horas = [time(i).strftime('%H:%M')
             for i in range(7, 22)]  # Lista de horas de 07:00 a 22:00

    if request.method == 'POST':
        docente_id = request.POST.get('docente_sel')
        try:
            docente_seleccionado = docente.objects.get(id=docente_id)
            
            ghs= obtenerGruposHorariosDocentes(docente_seleccionado)
            
            for gh in ghs:
                horarios = horario.objects.filter(fk_grupo_horario_id=gh[3])
                for disp in horarios:
                    dia_nombre = disp.día_id
                    dia_nombre_f=dia_semana.objects.get(id=dia_nombre)
                    
                    hora_inicio = disp.hora_de_inicio
                    hora_de_inicio_obj = datetime.strptime(hora_inicio, '%H:%M:%S')
                    hora_iniciof = hora_de_inicio_obj.strftime('%H:%M')

                    hora_fin = disp.hora_final
                    hora_fin_obj = datetime.strptime(hora_fin, '%H:%M:%S')
                    hora_finf = hora_fin_obj.strftime('%H:%M')

                    amb= disp.ambiente
                    curgh=grupo_horario.objects.get(id=gh[3])

                    horario_final.append((dia_nombre_f.dia_nombre, hora_iniciof, hora_finf,amb.nombre_ambiente,curgh.fk_curso, curgh.grupo, curgh.fk_curso.ciclo_curso))

        except docente.DoesNotExist:
            pass

        dias_semana = list(dia_semana.objects.values_list('dia_nombre', flat=True))
        return render(request, 'horarioDocentes.html', 
            {
             'docentes': docentes,
             'horario': horario_final,
             'dias_semana': dias_semana,
             #!agregado
             'horas': horas,  # Pasa la lista de horas a la plantilla
             'docente_id': int(docente_id),
         })
    
    else:
        return render(request, 'horarioDocentes.html', {
            'docentes': docentes,
        })


def asignacion_docente(request):

    if request.method == 'POST':

        horario.objects.all().delete()
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
        dias_seleccionados = request.POST.getlist('dias')  # Obtener días seleccionados
        
        if not dias_seleccionados:
            # Manejar el caso en que no se selecciona ningún día
            error = "Debes seleccionar al menos un día."
            return render(request, 'asignacion.html', {'dias': dias, 'error': error})  

        dias = dia_semana.objects.filter(dia_nombre__in=dias_seleccionados)
        print(dias)

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

            for clave, valor in horario_vars.items():
                    if solver.Value(valor) == 1:
                        grupo_id, nombre_ambiente, dia_nombre, hora_inicio, _ = clave  # Desempaqueta la clave

                        # Obtén los objetos de la base de datos correspondientes
                        grupo = grupo_horario.objects.get(id=grupo_id)
                        ambiente_obj = ambiente.objects.filter(nombre_ambiente=nombre_ambiente).first()
                        dia_obj = dia_semana.objects.get(dia_nombre=dia_nombre)

                        # Crea y guarda el objeto horario
                        horario_obj = horario(
                            hora_de_inicio=time(hora_inicio, 0),  # Convierte hora_inicio a objeto time
                            hora_final=time(hora_inicio + 1, 0),  # Convierte hora_fin a objeto time
                            ambiente=ambiente_obj,
                            día=dia_obj,
                            fk_grupo_horario=grupo
                        )
                        horario_obj.save()
        else:
            print("No se pudo encontrar una solución óptima o factible.")
            
        return render(request,'asignacion.html')
    else:
        dias = dia_semana.objects.all()
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
            "dias":dias
        }
        
        return render(request,'asignacion.html', datos)
    
def horarioXCiclo(request):
    ciclos_distintos = horario.objects.select_related(
        'fk_grupo_horario__fk_curso'
    ).values(
        'fk_grupo_horario__fk_curso__ciclo_curso'
    ).distinct()
    listaCiclos = list(ciclos_distintos.values_list('fk_grupo_horario__fk_curso__ciclo_curso', flat=True))
    listaCiclos = [str(ciclo) for ciclo in listaCiclos]

    horas = [time(i).strftime('%H:%M') for i in range(7, 22)]  # Lista de horas de 07:00 a 22:00
    dias_semana = list(dia_semana.objects.values_list('dia_nombre', flat=True))

    ciclo_curso = None
    grupo_ciclo = None
    listaGrupos = []
    horario_final = []
    if request.method == 'POST':
        ciclo_curso = request.POST.get('ciclo_sel')
        grupo_ciclo = request.POST.get('grupo_sel')

        if ciclo_curso:
            listaGrupos = grupo_horario.objects.filter(fk_curso__ciclo_curso=ciclo_curso).values_list('grupo', flat=True).distinct()
            listaGrupos = [str(grupo) for grupo in listaGrupos]
        if ciclo_curso and grupo_ciclo:
            horarios = horario.objects.filter(
                fk_grupo_horario__fk_curso__ciclo_curso=ciclo_curso,
                fk_grupo_horario__grupo=grupo_ciclo
            ).select_related('fk_grupo_horario__fk_curso')

            horario_final = []
            for disp in horarios:
                dia_nombre = disp.día_id
                dia_nombre_f = dia_semana.objects.get(id=dia_nombre)

                hora_inicio = disp.hora_de_inicio
                hora_de_inicio_obj = datetime.strptime(hora_inicio, '%H:%M:%S')
                hora_iniciof = hora_de_inicio_obj.strftime('%H:%M')

                hora_fin = disp.hora_final
                hora_fin_obj = datetime.strptime(hora_fin, '%H:%M:%S')
                hora_finf = hora_fin_obj.strftime('%H:%M')

                amb = disp.ambiente
                curgh = grupo_horario.objects.get(id=disp.fk_grupo_horario_id)

                horario_final.append((dia_nombre_f.dia_nombre, hora_iniciof, hora_finf,
                                      amb.nombre_ambiente, curgh.fk_curso, curgh.grupo, curgh.fk_curso.ciclo_curso))
        else:
            horario_final = []

    return render(request, 'horarioPorCiclo.html', {
        'ciclos': listaCiclos,
        'grupos': listaGrupos,
        'horario': horario_final,
        'dias_semana': dias_semana,
        'horas': horas,
        'ciclo_curso': ciclo_curso,
        'grupo_ciclo': grupo_ciclo,
    })

def filtrar_ambientes_por_edificio(request):
    if request.method == 'POST':
        edificio_id = request.POST.get('edificio_id')
        ambientes = ambiente.objects.filter(FKedificio_id=edificio_id)
        ambientes_data = [{'id': amb.id, 'nombre': amb.nombre_ambiente} for amb in ambientes]
        return JsonResponse({'ambientes': ambientes_data})



#Reporte Horarios por Ambiente:
def horarios_por_ambiente(request):
    horario_final = None
    ambiente_id = None
    edificio_id = None
    semestre_id = None
    horarios_selected = []
    horario_final = []
    lista_semestres = ciclo_academico.objects.all()
    lista_edificios = edificio.objects.all()
    ids_ambiente = horario.objects.values_list('ambiente_id', flat=True).distinct()

    #! agregado
    horas = [time(i).strftime('%H:%M')
             for i in range(7, 22)]  # Lista de horas de 07:00 a 22:00

    
    
        
    semestre_select = request.POST.get('semestre_id')
    edificio_select = request.POST.get('edificio_id')
    ambiente_select = request.POST.get('ambiente_id')
    lista_ambientes = ambiente.objects.filter(id__in=ids_ambiente)

    
    if request.method == 'POST':
        

        if edificio_select:
            edif = edificio.objects.get(id=edificio_select)
            print ('edificio_select: ', edificio_select)
            print ('edif: ', edif.nombre_edificio)
            
            if ambiente_select and semestre_select:
                try:
                
                    amb = ambiente.objects.get(id=ambiente_select)
                    grupo_h_semestre = grupo_horario.objects.filter(fk_ciclo_id=semestre_select)
                    horarios = horario.objects.filter(ambiente_id=ambiente_select, fk_grupo_horario__in=grupo_h_semestre)
                    print(amb.nombre_ambiente)
                    for hor in horarios:
                        print ('hor: ', hor.día_id)
                        dia_nombre = hor.día_id
                        dia_nombre_f=dia_semana.objects.get(id=dia_nombre)
                        
                        hora_inicio = hor.hora_de_inicio
                        hora_de_inicio_obj = datetime.strptime(hora_inicio, '%H:%M:%S')
                        hora_iniciof = hora_de_inicio_obj.strftime('%H:%M')

                        hora_fin = hor.hora_final
                        hora_fin_obj = datetime.strptime(hora_fin, '%H:%M:%S')
                        hora_finf = hora_fin_obj.strftime('%H:%M')

                        grupo_h = grupo_horario.objects.get(id=hor.fk_grupo_horario_id)
                        print ('grupo_h: ', grupo_h.grupo)
                        curso_h = curso.objects.get(id=grupo_h.fk_curso_id)
                        print ('curso_h: ', curso_h.nombre_curso)

                        horario_final.append((dia_nombre_f.dia_nombre, hora_iniciof, hora_finf,amb.nombre_ambiente,curso_h, grupo_h.grupo, curso_h.ciclo_curso))

                except ambiente.DoesNotExist:
                    pass

                dias_semana = list(dia_semana.objects.values_list('dia_nombre', flat=True))
                return render(request, 'horarioAmbientes.html', 
                    {
                    'edificios': lista_edificios,
                    'edificio_seleccionado': int(edificio_select),
                    'semestre_sekcionado': semestre_select,
                    'semestres': lista_semestres,
                    'ambientes': lista_ambientes,
                    'horario': horario_final,
                    'dias_semana': dias_semana,
                    #!agregado
                    'horas': horas,  # Pasa la lista de horas a la plantilla
                    'ambiente_seleccionado': int(ambiente_select),
                })
            else:
                return render(request, 'horarioAmbientes.html', {
                    'edificios': lista_edificios,
                    'semestres': lista_semestres,
                    'ambientes': lista_ambientes,
                })

    else:
        return render(request, 'horarioAmbientes.html', {
                'edificios': lista_edificios,
                'semestres': lista_semestres,
                'ambientes': lista_ambientes,
            })


def obtenerCicloConcatenado_Obj(ciclo_seleccionado):
    ciclo_seleccion = ciclo_academico.objects.get(
                cic_año=ciclo_seleccionado.split(' - ')[0],
                cic_semestre=ciclo_seleccionado.split(' - ')[1])
    return ciclo_seleccion

def listadoGrupoHorario():
    grupos_horario = grupo_horario.objects.all()

    gruposhorarioarray=[]

    for grupo_obj in grupos_horario:
                g =  grupo_obj.grupo
                curso= grupo_obj.fk_curso
                cap= grupo_obj.capacidad
                ciclo= grupo_obj.fk_ciclo
                
                id= grupo_obj.id 
                gruposhorarioarray.append((ciclo,g,curso,cap, id))

    return gruposhorarioarray


def gestionarGrupoHorario(request):
    
    gruposhorarioarray=listadoGrupoHorario()

    if request.method == 'POST':
        
        
        return render(request, 'gestionarGrupoHorario.html', {
            'grupos_horario': gruposhorarioarray,
        })    
    else:
        
        return render(request, 'gestionarGrupoHorario.html', {
            'grupos_horario': gruposhorarioarray,
        })        
    
def obtenercurso():
    cursos = curso.objects.all()
    cursoarray = []
    for c in cursos:
        cursoarray.append(c.nombre_curso)
    return cursoarray

def obtenerciclo():
    ciclos = ciclo_academico.objects.all()
    cicloarray = []
    for ci in ciclos:
        cicloarray.append(f"{ci.cic_año} - {ci.cic_semestre}")
        #cicloarray.append(ci.cic_año)
    return cicloarray

def agregarGrupoHorario(request):
    cursos = obtenercurso()
    ciclos = obtenerciclo()

    if request.method == 'POST':
        grupo = request.POST.get('grupo')
        capacidad = request.POST.get('capacidad')
        ciclo = request.POST.get('ciclo')
        n_curso = request.POST.get('curso')
        
        fkcic = ciclo_academico.objects.get(cic_año=ciclo)
        fkcur = curso.objects.get(nombre_curso=n_curso)

        nuevo_grupo_horario = grupo_horario(
            grupo=grupo,
            capacidad=capacidad,
            fk_ciclo=fkcic,
            fk_curso=fkcur,
        )
        
        # Guardar el nuevo grupo horario en la base de datos
        nuevo_grupo_horario.save()

        return redirect('gestionarGrupoHorario') 
    
    else:
        return render(request, 'agregarGrupoHorario.html', {'cursos': cursos, 'ciclos': ciclos})


def modificarGrupoHorario(request, grupo_id):
    grupo_horario_obj = get_object_or_404(grupo_horario, id=grupo_id)
    cursos = obtenercurso()
    ciclos = obtenerciclo()

    if request.method == 'POST':
        grupo = request.POST.get('grupo')
        capacidad = request.POST.get('capacidad')
        ciclo = request.POST.get('ciclo')
        n_curso = request.POST.get('curso')
        
        # Separar el año y el semestre del ciclo seleccionado
        ciclo_año, ciclo_semestre = ciclo.split(' - ')
        fkcic = ciclo_academico.objects.get(cic_año=ciclo_año, cic_semestre=ciclo_semestre)
        fkcur = curso.objects.get(nombre_curso=n_curso)

        # Actualizar el grupo horario existente
        grupo_horario_obj.grupo = grupo
        grupo_horario_obj.capacidad = capacidad
        grupo_horario_obj.fk_ciclo = fkcic
        grupo_horario_obj.fk_curso = fkcur
        
        # Guardar los cambios en la base de datos
        grupo_horario_obj.save()

        return redirect('gestionarGrupoHorario') 
    
    else:
        return render(request, 'modificarGrupoHorario.html', {
            'grupo_horario': grupo_horario_obj,
            'cursos': cursos,
            'ciclos': ciclos
        })
    

def eliminarGrupoHorario(request, grupo_id):
    grupo = grupo_horario.objects.get(id=grupo_id)
    #grupo = get_object_or_404(grupo_horario, id=grupo_id)
    
    if request.method == 'POST':
        respuesta = request.POST.get('respuesta')
        if respuesta == '1':
            grupo.delete()
        return redirect('gestionarGrupoHorario')
    
    return render(request, 'eliminarGrupoHorario.html', {'grupo': grupo})