from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from modulo_horario.models import *
from modulo_curso.models import *
from modulo_ambiente.models import *
import json
from modulo_ambiente.forms import UploadCSVForm
from .models import ambiente
from .models import edificio
from .models import tipo_ambiente
from django.contrib import messages
import csv, io, openpyxl
# Create your views here.


# def ambiente(request):
#     return HttpResponse("ambientes disponibles")

def asignarAmbiente(request):
    return render(request,'asignarAmbiente.html')

#def csvAmbientes(request):
 #   return render(request,'csvAmbientes.html')

def obtenerSemestre(request):
    ciclos = ciclo_academico.objects.all()
    ciclos_list = list(ciclos.values('id', 'cic_año', 'cic_semestre'))
    return JsonResponse(ciclos_list, safe=False)

def obtenerEscuelas(request):
    escuelas = escuela.objects.all()
    escuelas_list = list(escuelas.values('id', 'nombre_escuela', 'director_escuela', 'fk_facultad_id'))
    return JsonResponse(escuelas_list, safe=False)

def obtenerCursosPorEscuela(request, escuela_id):
    try:
        cursos = curso.objects.filter(FKplan_estudio__fk_escuela_id=escuela_id)
        cursos_list = list(cursos.values('id', 'codigo_curso', 'nombre_curso', 'horas_totales', 'horas_practicas', 'horas_teoricas', 'ciclo_curso'))
        return JsonResponse(cursos_list, safe=False)
    except escuela.DoesNotExist:
        return JsonResponse({'error': 'La escuela no existe.'}, status=404)


def obtener_edificios_y_ambientes(request):
    edificios = edificio.objects.all()
    data = []

    for edif in edificios:
        ambientes = ambiente.objects.filter(FKedificio=edif).values('id','nombre_ambiente', 'capacidad_ambiente', 'estado_ambiente', 'piso')
        data.append({
            'id': edif.id,
            'nombre_edificio': edif.nombre_edificio,
            'ambientes': list(ambientes)
        })
    
    return JsonResponse(data, safe=False)
def obtener_edificio_id(request, nombre):
    #edificios = edificio.objects.filter(nombre_edificio=nombre)
    #edificio_list = list(edificios.values('id'))
    #return (edificio_list)
    #edificio_id = edificio_.id
    #return (edificio_id)
    
    try:
        return edificio.objects.get(nombre_edificio=nombre)
    except edificio.DoesNotExist:
        return None

    

def guardar_ambientes_seleccionados(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        id_escuela = data.get('id_escuela')
        print(id_escuela)
        ambientes_seleccionados = data.get('ambientes_seleccionados')
        print(ambientes_seleccionados)
        try:
            for id_ambiente in ambientes_seleccionados:
                # Intenta guardar cada ambiente seleccionado en la base de datos
                horarioEscuela.objects.create(FKescuela_id=id_escuela, FKambiente_id=id_ambiente)

        except Exception as e:
            # Si hay un error al guardar algún ambiente, devuelve un mensaje de error
            return JsonResponse({'error': f'Error al guardar los ambientes: {str(e)}'}, status=500)
        else:
            # Si todos los ambientes se han guardado correctamente, devuelve un mensaje de éxito
            return JsonResponse({'mensaje': 'Todos los ambientes se han guardado exitosamente.'})
    else:
        return JsonResponse({'error': 'Método no permitido.'}, status=405)

def upload_file(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            if 'excel_file' in request.FILES:
                excel_file = request.FILES['excel_file']
                workbook = openpyxl.load_workbook(excel_file)
                sheet = workbook.active
                try:
                    

                    # Skip the header
                    for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=1, max_col=sheet.max_column):
                        if row is None or all(cell is None for cell in row):
                            continue  # Skip empty rows
                        print(f"Procesando fila: {row}")
                        print(f"Procesando ed: {row[2]}")
                        ambientes = edificio.objects.all()
                        nro, nombre_ambiente, nombre_edificio, aforo, piso, nombre_tipo_ambiente = [cell.value for cell in row]
                
# Iterar y mostrar cada instancia
                       
                        if row[1] and row[2]:
                            nombre = row[1]
                           
                            tipoa= row[5]
                            
                            
                            edificio_id = row[2]
                            edificios = edificio.objects.filter(nombre_edificio=nombre_edificio)
                            if not edificios:
                                messages.error(request, f"No se encontró ningún edificio con el nombre '{nombre_edificio}'.")
                                continue
                            tipos_ambiente = tipo_ambiente.objects.filter(tipo_de_ambiente=nombre_tipo_ambiente)
                            if not tipos_ambiente:
                                messages.error(request, f"No se encontró ningún tipo de ambiente con el nombre '{nombre_tipo_ambiente}'.")
                                continue
                            
                            for edificio_obj in edificios:
                                for tipo_ambiente_obj in tipos_ambiente: 
                                    ambiente_obj = ambiente(
                                        nombre_ambiente=nombre_ambiente,
                                        capacidad_ambiente=aforo,
                                        estado_ambiente='D',  # Asumiendo que todos los ambientes están disponibles por defecto
                                        piso=piso,
                                        FKedificio=edificio_obj,
                                        FKtipo_ambiente=tipo_ambiente_obj
                                        )
                                    ambiente_obj.save()
                            messages.success(request, 'Los datos han sido cargados exitosamente.')
            
                           
                        else:
                            messages.warning(request, f'Fila incompleta o incorrecta: {row}')
                    messages.success(
                        request, 'Archivo Excel subido correctamente')
                except openpyxl.utils.exceptions.InvalidFileException:
                    messages.error(
                        request, 'El archivo subido no es un archivo Excel válido.')
                except Exception as e:
                    messages.error(request, f'Error: {str(e)}')

            return redirect(request.path)
    else:
        form = UploadCSVForm()

    return render(request, './csvAmbientes.html', {'form': form})


#Para obtener los ambientes asignados a cada escuela:
def obtener_edificios_y_ambientes_semestre_ciclo_academico(request):

    if request.method == 'POST':
        data = json.loads(request.body)
        semestre = data.get('semestre')
        escuela = data.get('escuela')

        ambientes_por_edificios = obtener_edificios_y_ambientes_seleccion(semestre, escuela)
        return JsonResponse(ambientes_por_edificios, safe=False)
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)

#Llama a esta función:
def obtener_edificios_y_ambientes_seleccion(semestre_select, escuela_select):
    edificios = edificio.objects.all()

    
    
    ambientelist = []
    data = []

    for edif in edificios:
        
        ambientes = []
        

        if escuela_select and semestre_select:
            #escuela_se = escuela.objects.get(nombre_escuela="Ing. de sistemas")
            #semestre_se_split = str('2024 - 1').split(" - ")
            escuela_se = escuela.objects.get(id=escuela_select)
            semestre_se = ciclo_academico.objects.get(id=semestre_select)
            try:    
                escuela_ambiente_filtradas = escuela_ambiente.objects.filter(FK_ciclo_academico=semestre_se, FK_escuela=escuela_se)
            except escuela.DoesNotExist:
                grupo_ambientes = ambiente.objects.none()
            except ciclo_academico.DoesNotExist:
            #Maneja el caso en que el ciclo académico no existe
                grupo_ambientes = ambiente.objects.none()
            
            

            if escuela_ambiente_filtradas:
                ambiente_ids = escuela_ambiente_filtradas.values_list('FK_ambiente_id', flat=True)
                grupo_ambientes = ambiente.objects.filter(FKedificio=edif)
                
                for amb in grupo_ambientes:
                    if amb.id in ambiente_ids:
                        boton = str("ocupado")
                    else:
                        boton = str("no ocupado")
                    ambientes.append({
                            'id': amb.id,
                            'nombre_ambiente': amb.nombre_ambiente,
                            'capacidad_ambiente': amb.capacidad_ambiente,
                            'estado_ambiente': amb.estado_ambiente,
                            'piso': amb.piso,
                            'estado': boton
                        })
                      
                

            else:
                grupo_ambientes = ambiente.objects.filter(FKedificio=edif)
                for amb in grupo_ambientes:
                    boton = str("no ocupado")
                    ambientes.append({
                    'id': amb.id,
                    'nombre_ambiente': amb.nombre_ambiente,
                    'capacidad_ambiente': amb.capacidad_ambiente,
                    'estado_ambiente': amb.estado_ambiente,
                    'piso': amb.piso,
                    'estado': boton
                })

        else:
            grupo_ambientes = ambiente.objects.filter(FKedificio=edif)
            
            for amb in grupo_ambientes:
                boton = str("no ocupado")
                ambientes.append({
                    'id': amb.id,
                    'nombre_ambiente': amb.nombre_ambiente,
                    'capacidad_ambiente': amb.capacidad_ambiente,
                    'estado_ambiente': amb.estado_ambiente,
                    'piso': amb.piso,
                    'estado': boton
                })
        


        data.append({
            'id': edif.id,
            'nombre_edificio': edif.nombre_edificio,
            'ambientes': list(ambientes)
        })

    return data


#Proceso de asignar ambientes a escuelas.
#Falta configurar para enviar un mensaje para que se muestre en la pantalla y para bloquear/desbloquear el botón.
def guardar_ambientes_seleccionados(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print("Datos recibidos:", data)
        escuela_id = data.get('id_escuela')
        semestre_id = data.get('id_semestre')
        ambientes_seleccionados = data.get('ambientes_seleccionados')
        print("ID Escuela:", escuela_id)  # Mensaje de depuración
        print("ID Semestre:", semestre_id)  # Mensaje de depuración
        print("Ambientes seleccionados:", ambientes_seleccionados)
        

        try:
            escuela_se = get_object_or_404(escuela, id=escuela_id)
            semestre_se = get_object_or_404(ciclo_academico, id=semestre_id)
            escuela_ambiente_filtradas = escuela_ambiente.objects.filter(FK_ciclo_academico=semestre_se, FK_escuela=escuela_se)
            ambiente_ids = escuela_ambiente_filtradas.values_list('FK_ambiente_id', flat=True)
            print(str(ambiente_ids))

            for ambiente_data in ambientes_seleccionados:
                ambiente_id = ambiente_data.get('id')
                buttonClasses = str(ambiente_data.get('buttonClasses'))

                if int(ambiente_id) in ambiente_ids:
                    
                    if buttonClasses == 'success':
                        ambiente_se = get_object_or_404(ambiente, id=ambiente_id)
                        print('eliminando')
                        escuela_ambiente.objects.filter(FK_ciclo_academico=semestre_se, FK_escuela=escuela_se, FK_ambiente = ambiente_se).delete()
                else:
                    
                    if buttonClasses == 'danger':
                        print('creando')
                        ambiente_se = get_object_or_404(ambiente, id=ambiente_id)
                        escuela_ambiente.objects.create(
                            FK_escuela = escuela_se,
                            FK_ambiente = ambiente_se,
                            FK_ciclo_academico = semestre_se
                        )
                    
            return JsonResponse({'status': 'success'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)