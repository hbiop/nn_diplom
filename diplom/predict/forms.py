from django import forms

from predict.models import PredictSession

from datasets.models import DataFile
from learning.models import TrainingSession


class PredictSessionForm(forms.ModelForm):
    class Meta:
        model = PredictSession
        fields = ['title', 'model', 'dataset']
    title = forms.CharField(label="Название", max_length=255)
    model = forms.ModelChoiceField(
        label="Обученная модель",
        queryset=TrainingSession.objects.all(),
        empty_label="Выберите модель"
    )
    dataset = forms.ModelChoiceField(
        label="Набор данных",
        queryset=DataFile.objects.all(),
        empty_label="Выберите модель"
    )
