# Archivo: tareas/management/commands/crear_backup.py
import os
import shutil
import time
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Genera una copia de seguridad de la base de datos SQLite y limpia las viejas.'

    def handle(self, *args, **options):
        # 1. Configuración
        db_path = settings.DATABASES['default']['NAME']
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        
        # 2. Crear carpeta de backups si no existe
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            self.stdout.write(self.style.SUCCESS(f'Carpeta creada: {backup_dir}'))

        # 3. Generar nombre del archivo con fecha y hora
        fecha_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_filename = f"db_backup_{fecha_str}.sqlite3"
        backup_path = os.path.join(backup_dir, backup_filename)

        # 4. Copiar la base de datos
        try:
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                self.stdout.write(self.style.SUCCESS(f'✅ Backup creado exitosamente: {backup_filename}'))
            else:
                self.stdout.write(self.style.ERROR(f'⛔ No se encontró la base de datos en: {db_path}'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'⛔ Error al copiar: {str(e)}'))
            return

        # 5. Limpieza automática (Borrar backups de más de 30 días)
        self.limpiar_backups_antiguos(backup_dir)

    def limpiar_backups_antiguos(self, directorio):
        dias_a_mantener = 30
        ahora = time.time()
        eliminados = 0

        for archivo in os.listdir(directorio):
            ruta_completa = os.path.join(directorio, archivo)
            
            # Solo procesamos archivos .sqlite3
            if os.path.isfile(ruta_completa) and archivo.endswith('.sqlite3'):
                # Obtenemos la fecha de creación del archivo
                fecha_archivo = os.path.getmtime(ruta_completa)
                
                # Si es más viejo que 30 días (30 * 86400 segundos)
                if ahora - fecha_archivo > (dias_a_mantener * 86400):
                    try:
                        os.remove(ruta_completa)
                        eliminados += 1
                        self.stdout.write(f'🗑️ Backup antiguo eliminado: {archivo}')
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'No se pudo borrar {archivo}: {e}'))
        
        if eliminados > 0:
            self.stdout.write(self.style.SUCCESS(f'🧹 Limpieza completada: {eliminados} archivos antiguos borrados.'))