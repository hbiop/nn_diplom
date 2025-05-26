from django import forms
from .models import MLModel

class MLModelForm(forms.ModelForm):
    class Meta:
        model = MLModel
        fields = ['title', 'description', 'parameters']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'parameters': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': 'Введите параметры в формате JSON'
            }),
        }