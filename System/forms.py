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

