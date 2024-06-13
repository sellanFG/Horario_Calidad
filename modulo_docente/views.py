from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.contrib import messages
import csv, io, openpyxl
from .models import disponibilidad_docente
from .forms import dispo_form,UploadCSVForm
from datetime import datetime, time

from modulo_docente.models import docente, departamento_academico
from modulo_curso.models import escuela
from modulo_horario.models import ciclo_academico
from modulo_curso.models import curso
from modulo_curso.models import plan_estudio
from modulo_horario.models import grupo_horario, dia_semana
from modulo_docente.models import docente_grupo



# Create your views here.

def upload_file(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        enviar=disponibilidad_docentes()
        if form.is_valid():
            enviar=disponibilidad_docentes()

            if 'Subir_archivo_excel' in request.FILES:
                excel_file = request.FILES['Subir_archivo_excel']
                workbook = openpyxl.load_workbook(excel_file)
                sheet = workbook.active
                try:
                    for row in sheet.iter_rows(min_row=2, values_only=True):  # skip the header
                        if row[1] and row[2]:
                            horainicio = row[1] if isinstance(row[1], time) else datetime.strptime(row[1], '%H:%M:%S').time()
                            horafin = row[2] if isinstance(row[2], time) else datetime.strptime(row[2], '%H:%M:%S').time()
                            _, created = disponibilidad_docente.objects.update_or_create(
                                id=row[0],
                                ddo_horainicio=horainicio,
                                ddo_horafin=horafin,
                                FKdiasemana_id=row[3],
                                FKdocente_id=row[4],
                            ) 
                    messages.success(request, 'Archivo Excel subido correctamente')
                except Exception as e:
                    messages.error(request, 'Error: ' + str(e))
            else:
                messages.success(request, 'Debe subir un archivo para continuar')
                
            return redirect(request.path)
    else:
        form = UploadCSVForm()
        enviar=disponibilidad_docentes()
    return render(request, './csv.html', {'form': form, 'disponibilidad':enviar})



def disponibilidad_docentes():
    
    dispo= disponibilidad_docente.objects.all();    
    enviar=[]

    for dispobj in dispo:
        
        horariodispo=disponibilidad_docente.objects.get(id=dispobj.id)

        horaini= horariodispo.ddo_horainicio
        horafin= horariodispo.ddo_horafin
        dia= horariodispo.FKdiasemana
        docente = horariodispo.FKdocente
        
        enviar.append((horaini,horafin,dia,docente))


    return enviar


# Funciones útiles

def obtenerCicloConcatenado_Obj(ciclo_seleccionado):
    ciclo_seleccion = ciclo_academico.objects.get(
                cic_año=ciclo_seleccionado.split(' - ')[0],
                cic_semestre=ciclo_seleccionado.split(' - ')[1])
    return ciclo_seleccion

def obtenerGruposHorariosDocentePorEscuelaCiclo(escuela_seleccion, ciclo_seleccion):
    
    enviar=[]
    docentes=[]
    
    planes = plan_estudio.objects.filter(fk_escuela=escuela_seleccion)

    for plan_estudio_obj in planes:
        cursos_filtrados = curso.objects.filter(
            FKplan_estudio_id=plan_estudio_obj)

        for curso_obj in cursos_filtrados:
            gh = grupo_horario.objects.filter(
                fk_ciclo=ciclo_seleccion.id, fk_curso=curso_obj)
            
            
            for grupo_obj in gh:
                
                g_id = grupo_obj.id
                nombre = grupo_obj.fk_curso
                g_nombre = grupo_obj.grupo

                ghdocente= docente_grupo.objects.filter(FKgrupo=g_id)

                if not ghdocente:
                    enviar.append((curso_obj.codigo_curso, curso_obj.ciclo_curso,nombre, g_nombre, "No tiene docente asignado",g_id))

                else:

                    docentes = [ghdobj.FKdocente for ghdobj in ghdocente]
                    docentes_str = ', '.join(str(doc) for doc in sorted(docentes, key=lambda x: x.id))

                    enviar.append((curso_obj.codigo_curso, curso_obj.ciclo_curso,nombre, g_nombre, docentes_str,g_id))
    
    return enviar

def obtenerDocentesPorEstado(estado):
    
    enviardoc=[]
    
    docentes = docente.objects.filter(doc_estado=estado)
    
    for docente_obj in docentes:
                nombre = docente_obj.doc_nombres
                id= docente_obj.id
                enviardoc.append((nombre,id))

    return enviardoc

def obtenerDocentesAsignados(id):

    enviar=[]

    ghdocente= docente_grupo.objects.filter(FKgrupo=id)

    if not ghdocente:
            enviar.append(("No hay asignados"))
    else:
        
        for ghdobj in ghdocente:
            
            objeto=docente.objects.get(doc_nombres=ghdobj.FKdocente)
            enviar.append((objeto.id,objeto.doc_nombres))

    return enviar

# Asignacion carga Lectiva

def asignacionCargaLectiva(request):
    ciclos = ciclo_academico.objects.all()
    escuelas = escuela.objects.all()
    ciclo_seleccionado = request.POST.get('ciclo_ac')
    escuela_seleccionada = request.POST.get('esc')
    enviar = []
    enviardoc = []

    if request.method == 'POST':
        
        if ciclo_seleccionado and escuela_seleccionada:

            ciclo_seleccion = obtenerCicloConcatenado_Obj(ciclo_seleccionado)
            escuela_seleccion = escuela.objects.get(nombre_escuela=escuela_seleccionada)
            enviar= obtenerGruposHorariosDocentePorEscuelaCiclo(escuela_seleccion,ciclo_seleccion)
            enviardoc= obtenerDocentesPorEstado('D')
            

            datos = {
                'ciclo_select': ciclos,
                'escuela_select': escuelas,
                'ciclo_seleccionado': ciclo_seleccion,
                'escuela_seleccionada': escuela_seleccionada,
                'cursos': enviar,
                'docentes': enviardoc
            }

            return render(request, 'asignacionCargaLectiva.html', datos)
        
        if  request.POST.getlist('docentes'):

            docentes = request.POST.getlist('docentes')
            grupo_id = request.POST.get('grupoid')
            cic2 = request.POST.get('ciclo_seleccionado')
            esc2 = request.POST.get('escuela_seleccionada')
            
            docentes_string = str(docentes)
            docentes_lista = docentes_string.split(',')

            gid= grupo_horario.objects.get(id=grupo_id)

            docente_grupo.objects.filter(FKgrupo=gid).delete()
            
            dg = None;

            for docente_id in docentes_lista:
                docc = docente_id.strip("[]'")

                if (docc!=""):
                    docobj= docente.objects.get(doc_nombres=docc)
                    dg = docente_grupo(FKdocente=docobj, FKgrupo=gid)
                    dg.save()

            ciclo_seleccionado2= cic2
            escuela_seleccionada2=esc2

            ciclo_seleccion = obtenerCicloConcatenado_Obj(ciclo_seleccionado2)
            escuela_seleccion = escuela.objects.get(nombre_escuela=escuela_seleccionada2)
            enviar= obtenerGruposHorariosDocentePorEscuelaCiclo(escuela_seleccion,ciclo_seleccion)
            enviardoc= obtenerDocentesPorEstado('D')
            
            datos = {
                'ciclo_select': ciclos,
                'escuela_select': escuelas,
                'ciclo_seleccionado': ciclo_seleccion,
                'escuela_seleccionada': escuela_seleccionada2,
                'cursos': enviar,
                'docentes': enviardoc,
            }

            return render(request, 'asignacionCargaLectiva.html', datos)
        
    else:
        datos = {
            'ciclo_select': ciclos,
            'escuela_select': escuelas
        }
        return render(request, 'asignacionCargaLectiva.html', datos)

def disponibilidadDocente(request):
    docentes = docente.objects.all()
    horario_final = None
    docente_id = None
    #! agregado
    horas = [time(i).strftime('%H:%M')
             for i in range(7, 23)]  # Lista de horas de 07:00 a 22:00

    if request.method == 'POST':
        docente_id = request.POST.get('docente_sel')
        try:
            docente_seleccionado = docente.objects.get(id=docente_id)

            disponibilidades = disponibilidad_docente.objects.filter(
                FKdocente=docente_seleccionado)

            # Lista para almacenar tuplas (día, hora_inicio, hora_fin)
            horario_final = []

            for disp in disponibilidades:
                dia_nombre = disp.FKdiasemana.dia_nombre
                hora_inicio = disp.ddo_horainicio.strftime('%H:%M')
                hora_fin = disp.ddo_horafin.strftime('%H:%M')
                horario_final.append((dia_nombre, hora_inicio, hora_fin))
            
        except docente.DoesNotExist:
            pass

        dias_semana = list(dia_semana.objects.values_list('dia_nombre', flat=True))
        return render(request, 'disponibilidadDocente.html', {
            'docentes': docentes,
            'horario': horario_final,
            'dias_semana': dias_semana,
            #!agregado
            'horas': horas,  # Pasa la lista de horas a la plantilla
            'docente_id': int(docente_id),
        })
    
    else:
        return render(request, 'disponibilidadDocente.html', {
            'docentes': docentes,
        })



def cargaAcademicaDocente(request):
    
    
    if request.method == 'POST':
        
        return render(request, 'cargaAcademicaDocente.html')
    else:
        return render(request, 'cargaAcademicaDocente.html')
        