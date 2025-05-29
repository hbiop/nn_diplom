
from django.db import models

from datasets.models import DataFile

from learning.models import TrainingSession
from django.utils import timezone

# Create your models here.

class PredictSession(models.Model):
    title = models.CharField(max_length=255, default="")
    dataset = models.ForeignKey(DataFile, on_delete=models.CASCADE)
    model = models.ForeignKey(TrainingSession, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(default=timezone.now)
    logs = models.TextField(blank=True)

class PredictionResult(models.Model):
    session = models.ForeignKey(PredictSession, on_delete=models.CASCADE, related_name='results')
    input_data = models.JSONField()
    prediction = models.JSONField()