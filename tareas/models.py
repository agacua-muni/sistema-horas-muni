# Archivo: tareas/models.py
from django.db import models

class Tarea(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título de la tarea")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    horas = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, verbose_name="Horas Invertidas")
    fecha = models.DateField(auto_now_add=True, verbose_name="Fecha de Registro")
    completada = models.BooleanField(default=False, verbose_name="¿Completada?")

    class Meta:
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"
        ordering = ['-fecha']  # Ordenar de la más nueva a la más vieja

    def __str__(self):
        return f"{self.titulo} ({self.horas} hs)"