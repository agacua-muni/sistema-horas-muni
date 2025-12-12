# Archivo: tareas/admin.py
import os
import io
import base64
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.template.loader import get_template
from django.contrib.staticfiles import finders
from django.db.models import Sum
from django.utils.html import format_html
from xhtml2pdf import pisa
from simple_history.admin import SimpleHistoryAdmin 

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin
from .models import Secretaria, Departamento, Empleado, Periodo, RegistroHora

# ========================================================
# 1. UTILIDADES
# ========================================================
def link_callback(uri, rel):
    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)): result = [result]
        result = list(os.path.realpath(path) for path in result)
        path = result[0]
    else:
        sUrl = settings.STATIC_URL; sRoot = settings.STATIC_ROOT
        mUrl = settings.MEDIA_URL; mRoot = settings.MEDIA_ROOT
        if uri.startswith(mUrl): path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl): path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else: return uri
    if not os.path.isfile(path): raise Exception('media URI must start with %s or %s' % (sUrl, mUrl))
    return path

# ========================================================
# 2. REPORTES GRÁFICOS Y DE LISTADO (Sin Cambios)
# ========================================================

@admin.action(description='📊 Reporte Estadístico (Gráficos)')
def generar_estadisticas(modeladmin, request, queryset):
    periodo_actual = Periodo.objects.filter(vigente=True).first()
    if not periodo_actual: return HttpResponse("Error: No hay período vigente.", content_type='text/plain')

    # BARRAS
    periodos_historicos = Periodo.objects.filter(fecha_inicio__lte=periodo_actual.fecha_inicio).order_by('-fecha_inicio')[:6]
    periodos_historicos = sorted(periodos_historicos, key=lambda p: p.fecha_inicio)
    nombres_periodos = []; totales_periodos = []; lista_datos_barras = [] 

    for p in periodos_historicos:
        total = RegistroHora.objects.filter(periodo=p).aggregate(Sum('cantidad_horas'))['cantidad_horas__sum'] or 0
        nombres_periodos.append(p.nombre); totales_periodos.append(total)
        lista_datos_barras.append({'periodo': p.nombre, 'horas': total})

    plt.figure(figsize=(10, 3.5))
    plt.bar(nombres_periodos, totales_periodos, color='#007bff', width=0.5)
    plt.grid(axis='y', linestyle='--', alpha=0.5); plt.tight_layout()
    buffer_barras = io.BytesIO(); plt.savefig(buffer_barras, format='png'); plt.close()
    grafico_barras_b64 = base64.b64encode(buffer_barras.getvalue()).decode('utf-8')

    # TORTA
    datos_secretarias = RegistroHora.objects.filter(periodo=periodo_actual).values('empleado__departamento__secretaria__nombre').annotate(total=Sum('cantidad_horas'))
    labels = []; sizes = []; colors = []; lista_datos_torta = [] 
    color_map = {'gobierno': '#dc3545', 'ciudadania': '#ffc107', 'ciudadanía': '#ffc107', 'obras': '#0056b3', 'modernizacion': '#28a745', 'modernización': '#28a745'}
    total_absoluto = sum(item['total'] for item in datos_secretarias)

    for item in datos_secretarias:
        nombre_sec = item['empleado__departamento__secretaria__nombre'] or "Sin Secretaría"
        total_hs = item['total']
        if total_hs > 0:
            labels.append(nombre_sec); sizes.append(total_hs)
            nombre_lower = nombre_sec.lower(); c = '#6c757d' 
            if 'gobierno' in nombre_lower: c = color_map['gobierno']
            elif 'ciudadan' in nombre_lower: c = color_map['ciudadania']
            elif 'obra' in nombre_lower: c = color_map['obras']
            elif 'moderniza' in nombre_lower: c = color_map['modernizacion']
            colors.append(c)
            porc = round((total_hs / total_absoluto) * 100, 1)
            lista_datos_torta.append({'label': nombre_sec, 'value': total_hs, 'color': c, 'porcentaje': porc})

    plt.figure(figsize=(8, 4))
    if sizes: plt.pie(sizes, labels=None, colors=colors, startangle=140); plt.axis('equal') 
    else: plt.text(0.5, 0.5, 'Sin datos', ha='center')
    plt.tight_layout(); buffer_torta = io.BytesIO(); plt.savefig(buffer_torta, format='png'); plt.close()
    grafico_torta_b64 = base64.b64encode(buffer_torta.getvalue()).decode('utf-8')

    contexto = {'fecha_hoy': datetime.date.today(), 'periodo_actual': periodo_actual.nombre, 'grafico_barras': grafico_barras_b64, 'grafico_torta': grafico_torta_b64, 'datos_barras': lista_datos_barras, 'datos_torta': lista_datos_torta}
    template = get_template('admin/tareas/registrohora/estadisticas_pdf.html')
    html = template.render(contexto)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Estadisticas_{periodo_actual.nombre}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisa_status.err: return HttpResponse('Error PDF Gráfico.')
    return response

def generar_pdf_base(queryset, destinatario_nombre, destinatario_cargo):
    periodo_obj = Periodo.objects.filter(vigente=True).first()
    if not periodo_obj and queryset.exists(): periodo_obj = queryset.first().periodo

    datos_agrupados = {}; total_general = 0
    for registro in queryset:
        empleado = registro.empleado
        if empleado.id not in datos_agrupados:
            imputacion_texto = str(empleado.departamento) if empleado.departamento else "-"
            datos_agrupados[empleado.id] = {'nombre_completo': f"{empleado.apellido}, {empleado.nombre}", 'dni': empleado.dni, 'imputacion': imputacion_texto, 'total_horas': 0}
        datos_agrupados[empleado.id]['total_horas'] += registro.cantidad_horas
        total_general += registro.cantidad_horas

    lista_final = list(datos_agrupados.values()); lista_final.sort(key=lambda x: x['nombre_completo'])
    contexto = {'periodo': periodo_obj, 'fecha_hoy': datetime.date.today(), 'datos': lista_final, 'total_general': total_general, 'destinatario_nombre': destinatario_nombre, 'destinatario_cargo': destinatario_cargo}
    template = get_template('admin/tareas/registrohora/reporte_pdf.html')
    html = template.render(contexto)
    response = HttpResponse(content_type='application/pdf')
    filename = f"Reporte_{periodo_obj.nombre if periodo_obj else 'Horas'}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisa_status.err: return HttpResponse('Error al generar PDF.')
    return response

@admin.action(description='📄 Reporte para ANDREA (Sueldos)')
def reporte_andrea(modeladmin, request, queryset): return generar_pdf_base(queryset, "SRA. BALTIERI ANDREA SOLEDAD", "A/C del Área Sueldos")

@admin.action(description='📄 Reporte para EDITH (Sueldos)')
def reporte_edith(modeladmin, request, queryset): return generar_pdf_base(queryset, "SRA. SHORT EDITH MARISA", "Encargada del Área Sueldos")

# ========================================================
# 3. REPORTE AUDITORÍA (PDF SEGURO) - CON FILTRO
# ========================================================
@admin.action(description='🕵️ Descargar Auditoría de Cambios (PDF Seguro)')
def descargar_auditoria_pdf(modeladmin, request, queryset):
    """
    Genera un PDF con historial.
    FILTRO: Solo incluye registros con ediciones o borrados. Ignora los "Originales" limpios.
    """
    lista_auditoria = []
    
    periodos_ids = queryset.values_list('periodo_id', flat=True).distinct()

    # 1. Procesar registros ACTIVOS (Buscando Ediciones)
    for registro in queryset:
        # FILTRO CLAVE: Si tiene 1 o menos registros históricos, es Original (nunca se editó).
        # Lo saltamos para no ensuciar el reporte.
        if registro.history.count() <= 1:
            continue

        historial = registro.history.all().order_by('-history_date')
        
        for i in range(len(historial)):
            record = historial[i]
            
            item = {
                'fecha': record.history_date.strftime("%d/%m/%Y"),
                'hora': record.history_date.strftime("%H:%M"),
                'usuario': record.history_user.username if record.history_user else "Sistema",
                'empleado': f"{record.empleado.apellido}, {record.empleado.nombre}",
                'sort_key': record.history_date
            }

            if i == len(historial) - 1:
                # Creación (Lo mostramos para dar contexto de cuándo empezó la historia de este registro editado)
                item['accion'] = "✅ CREACIÓN"
                item['detalle'] = "Carga inicial"
                item['valor_ant'] = "-"
                item['valor_nue'] = f"{record.cantidad_horas} hs"
                lista_auditoria.append(item)
            else:
                # Edición
                previo = historial[i+1]
                delta = record.diff_against(previo)
                for change in delta.changes:
                    if change.field == 'cantidad_horas':
                        c_item = item.copy()
                        c_item['accion'] = "⚠️ EDICIÓN"
                        c_item['detalle'] = "Modificación de Cantidad"
                        c_item['valor_ant'] = f"{change.old} hs"
                        c_item['valor_nue'] = f"{change.new} hs"
                        lista_auditoria.append(c_item)
                    elif change.field == 'imputacion':
                        c_item = item.copy()
                        c_item['accion'] = "⚠️ EDICIÓN"
                        c_item['detalle'] = "Cambio de Imputación"
                        c_item['valor_ant'] = str(change.old)
                        c_item['valor_nue'] = str(change.new)
                        lista_auditoria.append(c_item)

    # 2. Buscar registros BORRADOS (Papelera)
    borrados = RegistroHora.history.filter(
        history_type='-', 
        periodo_id__in=periodos_ids
    ).order_by('-history_date')

    for record in borrados:
        try: nombre_emp = f"{record.empleado.apellido}, {record.empleado.nombre}"
        except: nombre_emp = "Empleado Desconocido"

        item = {
            'fecha': record.history_date.strftime("%d/%m/%Y"),
            'hora': record.history_date.strftime("%H:%M"),
            'usuario': record.history_user.username if record.history_user else "Sistema",
            'empleado': nombre_emp,
            'accion': "❌ ELIMINADO",
            'detalle': "Registro eliminado",
            'valor_ant': f"{record.cantidad_horas} hs",
            'valor_nue': "0 hs",
            'sort_key': record.history_date
        }
        lista_auditoria.append(item)

    # 3. Ordenar y Generar PDF
    lista_auditoria.sort(key=lambda x: x['sort_key'], reverse=True)

    contexto = {
        'fecha_hoy': datetime.datetime.now(),
        'usuario_solicitante': request.user.username,
        'logs': lista_auditoria
    }

    template = get_template('admin/tareas/registrohora/auditoria_pdf.html')
    html = template.render(contexto)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Auditoria_Segura.pdf"'
    
    # link_callback para el logo
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisa_status.err: return HttpResponse('Error al generar PDF de Auditoría.')
    return response

# ========================================================
# 4. RESOURCES & ADMINS
# ========================================================
class DepartamentoResource(resources.ModelResource):
    secretaria = fields.Field(column_name='secretaria', attribute='secretaria', widget=ForeignKeyWidget(Secretaria, field='imputacion'))
    class Meta: model = Departamento; fields = ('nombre', 'imputacion', 'secretaria'); import_id_fields = ('nombre',)

class EmpleadoResource(resources.ModelResource):
    dni = fields.Field(column_name='Nº identificación', attribute='dni')
    departamento = fields.Field(column_name='Departamento', attribute='departamento', widget=ForeignKeyWidget(Departamento, field='nombre'))
    def before_import_row(self, row, **kwargs):
        nombre = row.get('Nombre del empleado', '')
        if nombre:
            try: p = nombre.split(','); row['apellido'] = p[0].strip(); row['nombre'] = p[1].strip() if len(p)>1 else "-"
            except: pass
    class Meta: model = Empleado; fields = ('dni', 'apellido', 'nombre', 'departamento'); import_id_fields = ('dni',)

@admin.register(Secretaria)
class SecretariaAdmin(admin.ModelAdmin):
    list_display = ('imputacion', 'nombre'); search_fields = ('nombre', 'imputacion'); ordering = ('imputacion',)

@admin.register(Departamento)
class DepartamentoAdmin(ImportExportModelAdmin):
    resource_class = DepartamentoResource; list_display = ('imputacion', 'nombre', 'secretaria'); list_filter = ('secretaria',); search_fields = ('nombre', 'imputacion'); ordering = ('imputacion',)

@admin.register(Empleado)
class EmpleadoAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = EmpleadoResource; list_display = ('dni', 'apellido', 'nombre', 'departamento'); list_filter = ('departamento',); search_fields = ('apellido', 'nombre', 'dni'); ordering = ('apellido',)

@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin', 'vigente', 'cerrado'); list_filter = ('vigente', 'cerrado'); list_editable = ('vigente', 'cerrado'); ordering = ('-fecha_inicio',)

@admin.register(RegistroHora)
class RegistroHoraAdmin(SimpleHistoryAdmin):
    change_list_template = 'admin/tareas/registrohora/change_list.html'
    
    list_display = ('empleado', 'cantidad_horas', 'imputacion_real', 'estado_auditoria')
    list_filter = ('periodo', 'empleado__departamento', 'otro_departamento')
    search_fields = ('empleado__apellido', 'empleado__dni')
    fields = ('periodo', 'empleado', 'cantidad_horas', 'otro_departamento', 'autorizado_exceso')
    
    actions = [reporte_andrea, reporte_edith, generar_estadisticas, descargar_auditoria_pdf]

    def estado_auditoria(self, obj):
        if obj.history.count() > 1: return format_html('<span style="color:orange; font-weight:bold;">⚠️ Editado</span>')
        return format_html('<span style="color:green;">✅ Original</span>')
    estado_auditoria.short_description = "Estado Carga"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}; extra_context['periodo_vigente'] = Periodo.objects.filter(vigente=True).first()
        return super().changelist_view(request, extra_context=extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "periodo":
            kwargs["queryset"] = Periodo.objects.filter(vigente=True)
            vigente = Periodo.objects.filter(vigente=True).first()
            if vigente: kwargs["initial"] = vigente
        return super().formfield_for_foreignkey(db_field, request, **kwargs)