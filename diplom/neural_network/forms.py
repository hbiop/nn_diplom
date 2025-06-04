from django import forms
from .models import MLModel

class LayerForm(forms.Form):
    units = forms.IntegerField(
        label="Количество нейронов",
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    activation = forms.ChoiceField(
        label="Функция активации",
        choices=[
            ('relu', 'ReLU'),
            ('sigmoid', 'Sigmoid'),
            ('tanh', 'Tanh'),
            ('softmax', 'Softmax'),
            ('linear', 'Linear'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class MLModelForm(forms.ModelForm):
    class Meta:
        model = MLModel
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
        }