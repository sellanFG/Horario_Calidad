from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.contrib import messages
import csv, io, openpyxl
from .models import disponibilidad_docente
from .forms import dispo_form,UploadCSVForm
from datetime import datetime, time

from modulo_docente.models import docente
from modulo_curso.models import escuela
from modulo_horario.models import ciclo_academico
from modulo_curso.models import curso
from modulo_curso.models import plan_estudio
from modulo_horario.models import grupo_horario
from modulo_docente.models import docente_grupo



# Create your views here.

def upload_file(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            if 'excel_file' in request.FILES:
                excel_file = request.FILES['excel_file']
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
                csv_file = request.FILES['csv_file']
                data_set = csv_file.read().decode('UTF-8')
                io_string = io.StringIO(data_set)
                next(io_string)
                try:
                    for column in csv.reader(io_string, delimiter=';', quotechar="|"):
                        if column[1] and column[2]:
                            horainicio = datetime.strptime(column[1], '%H:%M:%S').time()
                            horafin = datetime.strptime(column[2], '%H:%M:%S').time()
                            _, created = disponibilidad_docente.objects.update_or_create(
                                id=column[0],
                                ddo_horainicio=horainicio,
                                ddo_horafin=horafin,
                                FKdiasemana_id=column[3],
                                FKdocente_id=column[4],
                        ) 
                    messages.success(request, 'Archivo subido correctamente')
                except Exception as e:
                    messages.error(request, 'Error: ' + str(e))
            return redirect(request.path)
    else:
        form = UploadCSVForm()
    return render(request, './csv.html', {'form': form})