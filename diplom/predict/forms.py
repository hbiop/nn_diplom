from django import forms

from predict.models import PredictSession

from datasets.models import DataFile
from learning.models import TrainingSession


class PredictSessionForm(forms.ModelForm):
    class Meta:
        model = PredictSession
        fields = ['title', 'model', 'dataset']
    title = forms.CharField(max_length=255)
    model = forms.ModelChoiceField(
        queryset=TrainingSession.objects.all(),
        empty_label="Выберите модель"
    )
    dataset = forms.ModelChoiceField(
        queryset=DataFile.objects.all(),
        empty_label="Выберите модель"
    )
