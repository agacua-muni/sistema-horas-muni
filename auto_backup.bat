@echo off
:: Ir al disco C (o el que sea)
c:

:: Entrar a la carpeta de tu proyecto (Verifica que esta ruta sea la real)
cd "C:\Users\Ariel Acuña\Documents\Ariel\Ariel\FACULTAD\DIPLOMATURA\Proyecto_horas_muni"

:: Activar el entorno virtual y ejecutar el comando
call venv\Scripts\activate
python manage.py crear_backup

:: (Opcional) Esperar 5 segundos para ver si hubo error antes de cerrar, si lo pruebas manual
timeout /t 5