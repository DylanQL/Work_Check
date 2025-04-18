from django import forms
from .models import Position, Usuario, Template

class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['position_code', 'position_name']
        widgets = {
            'position_code': forms.TextInput(attrs={'class': 'form-control'}),
            'position_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Formulario actualizado que excluye administradores y gerentes
class UserTemplateAssignForm(forms.Form):
    user_id = forms.ModelChoiceField(
        queryset=Usuario.objects.exclude(user_type__in=['Administrador', 'Gerente']),
        label="Usuario",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    template_id = forms.ModelChoiceField(
        queryset=Template.objects.all(),
        label="Plantilla",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
class UserTemplateEditForm(forms.Form):
    template_id = forms.ModelChoiceField(
        queryset=Template.objects.all(),
        label="Plantilla",
        widget=forms.Select(attrs={'class': 'form-control'})
    )