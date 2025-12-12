import os

# Buscamos dónde estamos parados
carpeta_actual = os.getcwd()
print(f"\n--- 🕵️ DIAGNÓSTICO DE UBICACIÓN ---")
print(f"Estoy buscando en: {carpeta_actual}")

# Ruta esperada del archivo
ruta_archivo = os.path.join(carpeta_actual, 'templates', 'admin', 'import_export', 'import.html')

print(f"\nVerificando si existe el archivo mágico...")
print(f"Ruta: {ruta_archivo}")

if os.path.exists(ruta_archivo):
    print("\n✅ ¡ÉXITO! El archivo EXISTE en el lugar correcto.")
    print("Si no se ve el cartel verde, el problema está en settings.py")
else:
    print("\n❌ ERROR CRÍTICO: El archivo NO ESTÁ donde debería.")
    print("Posibles causas:")
    print("1. La carpeta 'templates' está metida dentro de 'core' o 'tareas' (debe estar suelta).")
    print("2. Escribiste 'import-export' con guion medio (debe ser 'import_export' con guion bajo).")