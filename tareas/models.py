# Archivo: tareas/models.py
from django.db import models
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords # <--- IMPORTANTE: Librería de auditoría

# ========================================================
# 1. SECRETARÍAS
# ========================================================
class Secretaria(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Secretaría", unique=True)
    imputacion = models.CharField(max_length=10, verbose_name="Imputación", default="00.00")

    class Meta:
        verbose_name = "Secretaría"
        verbose_name_plural = "Secretarías"
        ordering = ['imputacion']

    def __str__(self):
        return f"{self.imputacion} - {self.nombre}"

# ========================================================
# 2. DEPARTAMENTOS
# ========================================================
class Departamento(models.Model):
    secretaria = models.ForeignKey(Secretaria, on_delete=models.CASCADE, verbose_name="Secretaría")
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Departamento", unique=True)
    imputacion = models.CharField(max_length=10, verbose_name="Imputación", default="00")

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['secretaria', 'imputacion']

    def __str__(self):
        try:
            prefijo_sec = self.secretaria.imputacion.split('.')[0]
            codigo_final = f"{prefijo_sec}.{self.imputacion}"
        except:
            codigo_final = self.imputacion
        
        return f"{codigo_final} - {self.nombre}"

# ========================================================
# 3. EMPLEADOS
# ========================================================
class Empleado(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    dni = models.CharField(max_length=20, unique=True, verbose_name="DNI")
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, verbose_name="Departamento")
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")
    
    # AUDITORÍA (CAJA NEGRA)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

# ========================================================
# 4. PERÍODOS
# ========================================================
class Periodo(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Nombre del Período (Ej: Enero 2024)")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    
    cerrado = models.BooleanField(default=False, verbose_name="¿Cerrado Totalmente?")
    vigente = models.BooleanField(default=False, verbose_name="¿Es el Período Vigente?")

    class Meta:
        verbose_name = "Período"
        verbose_name_plural = "Períodos"
        ordering = ['-fecha_inicio']

    def __str__(self):
        estado_cerrado = "🔒 CERRADO" if self.cerrado else "🔓 ABIERTO"
        estado_vigente = "⭐ VIGENTE" if self.vigente else ""
        return f"{self.nombre} {estado_cerrado} {estado_vigente}"

    def save(self, *args, **kwargs):
        if self.vigente:
            Periodo.objects.filter(vigente=True).exclude(pk=self.pk).update(vigente=False)
        super().save(*args, **kwargs)

# ========================================================
# 5. HORAS DE CONTRATADOS
# ========================================================
class RegistroHora(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, verbose_name="Empleado")
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, verbose_name="Período")
    
    cantidad_horas = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Cantidad de Horas")
    fecha_carga = models.DateField(auto_now_add=True, verbose_name="Fecha de Carga")

    otro_departamento = models.ForeignKey(
        Departamento, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="¿Imputar a otra Área?",
        help_text="Seleccionar SOLO si las horas se cobran a un área distinta a la del empleado."
    )

    autorizado_exceso = models.BooleanField(
        default=False, 
        verbose_name="¿Autorizar Exceso (+180hs)?",
        help_text="Marcar para permitir cargar más de 180 horas."
    )

    # AUDITORÍA (CAJA NEGRA) - Aquí es donde ocurre la magia
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Hora de Contratado"
        verbose_name_plural = "Horas de Contratados"

    def __str__(self):
        return f"{self.empleado} - {self.cantidad_horas}hs ({self.periodo})"

    def imputacion_real(self):
        if self.otro_departamento:
            return f"⚠ {self.otro_departamento} (Prestado)"
        return self.empleado.departamento
    imputacion_real.short_description = "Imputación Final"

    # --- VALIDACIÓN SEGURA ---
    def clean(self):
        try:
            mi_periodo = self.periodo
        except Exception:
            return 

        # 1. Validar Período Cerrado
        if mi_periodo.cerrado:
            raise ValidationError(f"⛔ ERROR: El período '{mi_periodo.nombre}' está CERRADO.")

        # 2. Validar Tope (Mayor o igual a 180)
        if self.cantidad_horas and self.cantidad_horas >= 180 and not self.autorizado_exceso:
            raise ValidationError("⛔ ERROR: Al cargar 180 horas o más se requiere Autorización.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)