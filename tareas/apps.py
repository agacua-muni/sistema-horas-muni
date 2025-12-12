# Archivo: tareas/apps.py
from django.apps import AppConfig

class TareasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tareas'
    verbose_name = 'Módulos'  # <--- Esto cambia el nombre en el menú lateral