from django.db import models
import json

from django.urls import reverse
from django.conf import settings


class MLModel(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название модели")
    description = models.TextField(verbose_name="Описание")
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    parameters = models.JSONField(verbose_name="Параметры модели")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mlmodels'
    )
    class Meta:
        verbose_name = "Модель машинного обучения"
        verbose_name_plural = "Модели"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('model_detail', kwargs={'pk': self.pk})

    def formatted_parameters(self):
        return json.dumps(self.parameters, indent=4, ensure_ascii=False)