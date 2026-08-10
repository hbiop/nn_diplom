from django import forms

from predict.models import PredictSession

from datasets.models import DataFile
from learning.models import TrainingSession


class PredictSessionForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['model'].queryset = TrainingSession.objects.filter(user=user, status='completed')
            self.fields['dataset'].queryset = DataFile.objects.filter(user=user)

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
