import pandas as pd
from django import forms

from datasets.models import DataFile
from learning.models import TrainingSession
from neural_network.models import MLModel


class SessionForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['model'].queryset = MLModel.objects.filter(user=user)
            self.fields['dataset'].queryset = DataFile.objects.filter(user=user)

    class Meta:
        model = TrainingSession
        fields = ['title', 'model', 'dataset', 'epochs', 'learning_rate']
    title = forms.CharField(label="Название",max_length=255)
    model = forms.ModelChoiceField(
        label="Модель нейронной сети",
        queryset=MLModel.objects.all(),
        empty_label="Выберите модель"
    )
    dataset = forms.ModelChoiceField(
        label="Набор данных",
        queryset=DataFile.objects.all(),
        empty_label="Выберите модель"
    )
    epochs = forms.IntegerField(label="Количество эпох",min_value=1, max_value=10000)
    learning_rate = forms.FloatField(
        label="Скорость обучения",
        min_value=0.01,
        max_value=1
    )