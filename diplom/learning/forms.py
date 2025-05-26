import pandas as pd
from django import forms

from datasets.models import DataFile
from learning.models import TrainingSession
from neural_network.models import MLModel


class SessionForm(forms.ModelForm):
    class Meta:
        model = TrainingSession
        fields = ['title', 'model', 'dataset', 'epochs', 'learning_rate']
    title = forms.CharField(max_length=255)
    model = forms.ModelChoiceField(
        queryset=MLModel.objects.all(),
        empty_label="Выберите модель"
    )
    datasets = forms.ModelChoiceField(
        queryset=DataFile.objects.all(),
        empty_label="Выберите модель"
    )
    epochs = forms.IntegerField(min_value=1, max_value=10000)
    learning_field = forms.DecimalField(min_value=0.01, max_value=1)