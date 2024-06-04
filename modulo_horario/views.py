from pyexpat import model
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from datetime import date, datetime, timedelta
from modulo_curso.models import escuela , plan_estudio, curso
from modulo_horario.models import grupo_horario,dia_semana,horario
from modulo_docente.models import disponibilidad_docente, docente, docente_grupo
from pulp import LpMinimize, LpProblem, LpVariable, lpSum

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


def asignacion_docente(request):

    if request.method == 'POST':

        # Datos de entrada 
        # 1. Lista de docentes
        docentes = list(docente.objects.values_list('id', flat=True)) 

        # 2. Lista de grupos
        grupos = list(grupo_horario.objects.values_list('id', flat=True))

        # 3. Lista de días y horas
        dias = list(dia_semana.objects.values_list('dia_nombre', flat=True))
        horas = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"]

        disponibilidad = {}
        for docen in docente.objects.all():
            disponibilidad[docen.id] = {}  # Inicializar diccionario interno para cada docente
            for dd in disponibilidad_docente.objects.filter(FKdocente=docen):
                dia = dd.FKdiasemana.dia_nombre
                disponibilidad[docen.id].setdefault(dia, [])
                for hora in horas:
                    hora_objeto = datetime.strptime(hora, "%H:%M").time()
                    inicio_hora = hora_objeto
                    fin_hora = (datetime.combine(date.min, hora_objeto) + timedelta(hours=1)).time()
                    if dd.ddo_horainicio <= inicio_hora and dd.ddo_horafin >= fin_hora:
                        disponibilidad[docen.id][dia].append(hora)

        # 5. Diccionario de horas por curso
        horas_por_curso = {grupo.id: grupo.fk_curso.horas_totales 
                        for grupo in grupo_horario.objects.select_related('fk_curso')}

        # 6. Diccionario de tipo de curso
        tipo_curso = {grupo.id: grupo.fk_curso.FKtipocurso 
                    for grupo in grupo_horario.objects.select_related('fk_curso')}

        # 7. Diccionario de ciclo del curso
        ciclo_curso = {grupo.id: grupo.fk_curso.ciclo_curso 
                    for grupo in grupo_horario.objects.select_related('fk_curso')}


        # 8. Diccionario de docentes por grupo
        docentes_por_grupo = {}
        for dg in docente_grupo.objects.all():
            docentes_por_grupo.setdefault(dg.FKgrupo.id, []).append(dg.FKdocente.id)


        # Crear el problema de programación lineal
        problema = LpProblem("AsignacionHorarios", LpMinimize)

        # Crear las variables de decisión
        x = LpVariable.dicts("x",
                                ((i, k, l) for i in grupos for k in dias for l in horas),
                                cat='Binary')

        y = LpVariable.dicts("y", ((j, k) for j in docentes for k in dias), cat='Binary')

        z = LpVariable.dicts("z", ((i, k) for i in grupos for k in dias), cat='Binary')

        # Función objetivo (minimizar horas vacías)
        problema += lpSum(1 - y[j, k] for j in docentes for k in dias)

        # Restricciones
        # 1. Disponibilidad de los docentes
        for i in grupos:
            for k in dias:
                for j in docentes_por_grupo[i]:
                    horas_docente = disponibilidad.get(j, {}).get(k, [])
                    for l in horas:
                        if l not in horas_docente:
                            problema += x[i, k, l] == 0 

        # 2. Carga horaria de los cursos
        for i in grupos:
            problema += lpSum(x[i, k, l] for k in dias for l in horas) == horas_por_curso[i]

        # Asignación completa de horas por grupo
        for i in grupos:
            problema += lpSum(x[i, k, l] for k in dias for l in horas) == horas_por_curso[i]

        # for i in grupos:
        #      for k in dias:
        #          horas_ordenadas = sorted(set([h for (_, _, _, h) in disponibilidad if _ == i and __ == k]))
        #          for idx, l in enumerate(horas_ordenadas[:-1]):  # Iterar hasta la penúltima hora
        #              problema += x[i, k, l] - x[i, k, horas_ordenadas[idx + 1]] <= 0


        # 3. Relación entre x_igkl e y_jk
        for i in grupos:
            for k in dias:
                for l in horas:
                    problema += x[i, k, l] <= y[j, k] 

        # 4. Separación de 1 hora entre cursos virtuales y presenciales
        for k in dias:
            for l in range(len(horas) - 1):
                for i in grupos:
                    for j in grupos:
                        if i != j and tipo_curso[i] != tipo_curso[j]:
                            problema += x[i, k, l] + x[j, k, l + 1] <= 1

       #5. Preferencia de horario según ciclo del curso (heurística)
        for i in grupos:
            for k in dias:
                for l in horas:
                    hora_inicio = int(l.split("-")[0].split(":")[0])  # Extraer hora de inicio y convertir a entero
                    if ciclo_curso[i] % 2 == 0 and hora_inicio <= 12:  # Curso impar en la mañana
                        problema += x[i, k, l] <= 0.5  # Penalización suave
                    elif ciclo_curso[i] % 2 == 1 and hora_inicio > 12:  # Curso par en la tarde
                        problema += x[i, k, l] <= 0.5  # Penalización suave

        # 6. No superposición de horarios para un mismo docente
        for j in docentes:
            for k in dias:
                for l in horas:
                    problema += lpSum(x[i, k, l] for i in grupos if j in docentes_por_grupo[i]) <= 1

        # 7. Máximo de 2 días de clases por grupo (con variable auxiliar)
        for i in grupos:
            for k in dias:
                # Relación entre x_igkl y w_ik
                problema += lpSum(x[i, k, l] for l in horas) <= len(horas) * z[i, k]
                # Asegurar que w_ik sea 1 si hay alguna hora asignada en el día k
                problema += lpSum(z[i, k] >= x[i, k, l] for l in horas)

            # Límite de 2 días de clases por grupo
            problema += lpSum(z[i, k] for k in dias) <= 2

        # 8. Mínimo de 2 horas continuas por grupo
        for i in grupos:
            for k in dias:
                problema += lpSum(x[i, k, l] for l in horas) >= 2 * z[i, k]

        # Resolver el problema
        problema.solve()
        # Diccionario para almacenar los resultados
        resultados = {}

        # Almacenar los resultados en el diccionario
        for i in grupos:
            for k in dias:
                for l in horas:
                    if x[i, k, l].varValue == 1:
                        grupo = grupo_horario.objects.get(id=i).grupo
                        curso = grupo_horario.objects.get(id=i).fk_curso.nombre_curso
                        docente_nombre = docente.objects.get(id=[j for j in docentes_por_grupo[i]][0]).doc_nombres
                        if grupo not in resultados:
                            resultados[grupo] = []
                        resultados[grupo].append({
                            "curso": curso,
                            "dia": k,
                            "hora": l,
                            "docente": docente_nombre
                        })
        # Mostrar los resultados
        for i in grupos:
            for k in dias:
                for l in horas:
                    if x[i, k, l].varValue == 1:
                        print(f"Grupo {grupo_horario.objects.get(id=i).grupo} - Curso {grupo_horario.objects.get(id=i).fk_curso.nombre_curso} - Día {k} - Hora {l}  - Docente {docente.objects.get(id=[j for j in docentes_por_grupo[i]][0]).doc_nombres}")

        return render(request,'asignacion.html')
    else:
        return render(request,'asignacion.html')