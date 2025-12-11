# Archivo: tareas/admin.py
from django.contrib import admin
from .models import Tarea

# Esta clase permite configurar cómo se ve la lista en el panel
class TareaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'horas', 'fecha', 'completada') # Columnas visibles
    list_filter = ('completada', 'fecha') # Filtros laterales
    search_fields = ('titulo', 'descripcion') # Barra de búsqueda

# Registramos el modelo
admin.site.register(Tarea, TareaAdmin)