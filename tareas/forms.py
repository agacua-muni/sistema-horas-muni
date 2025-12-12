# Archivo: tareas/forms.py
from django import forms
from .models import Tarea

class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ['titulo', 'descripcion', 'horas'] # Campos que llenará el empleado
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Mantenimiento de servidores'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalles del trabajo realizado...'}),
            'horas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': '0.0'}),
        }