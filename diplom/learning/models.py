from datetime import datetime

from django.db import models

# Create your models here.
from django.db import models

from datasets.models import DataFile
from django.urls import reverse
from neural_network.models import MLModel


from django.db import models
from django.utils import timezone
from django.conf import settings

from .secure_pickle import dumps as secure_dumps, loads as secure_loads


class TrainingSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('running', 'Выполняется'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
    ]

    title = models.CharField(max_length=255, default="")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning'
    )
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE)
    dataset = models.ForeignKey(DataFile, on_delete=models.CASCADE)
    epochs = models.IntegerField(default=100)
    learning_rate = models.FloatField(default=0.01)
    creation_date = models.DateTimeField(default=timezone.now)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    current_epoch = models.IntegerField(default=0)
    progress = models.FloatField(default=0)

    preprocessor = models.BinaryField(null=True, blank=True)
    neural_network = models.BinaryField(null=True, blank=True)

    best_loss = models.FloatField(null=True, blank=True)
    final_accuracy = models.FloatField(null=True, blank=True)
    logs = models.TextField(blank=True)

    def get_absolute_url(self):
        return reverse('session_detail', kwargs={'pk': self.pk})

    def save_preprocessor(self, preprocessor):
        """Сериализация и сохранение препроцессора"""
        serialized = secure_dumps(preprocessor)
        self.preprocessor = serialized
        self.save()

    def load_preprocessor(self):
        """Десериализация препроцессора"""
        if not self.preprocessor:
            return None
        return secure_loads(self.preprocessor)

    def save_neural_network(self, nn):
        """Сериализация и сохранение нейронной сети"""
        serialized = secure_dumps(nn)
        self.neural_network = serialized
        self.save()

    def load_neural_network(self):
        """Десериализация нейронной сети"""
        if not self.neural_network:
            return None
        return secure_loads(self.neural_network)

    def get_epoch_history(self):
        """Возвращает историю эпох в виде списка словарей"""
        return list(self.epoch_history.all().values(
            'epoch_number',
            'loss',
            'accuracy',
            'val_loss',
            'val_accuracy',
            'timestamp'
        ).order_by('epoch_number'))

    def get_epoch_stats(self):
        """Возвращает статистику по эпохам"""
        from django.db.models import Avg, Max, Min
        return self.epoch_history.all().aggregate(
            min_loss=Min('loss'),
            max_accuracy=Max('accuracy'),
            avg_loss=Avg('loss'),
            avg_accuracy=Avg('accuracy')
        )

    def __str__(self):
        return self.title


class TrainingEpoch(models.Model):
    session = models.ForeignKey(
        TrainingSession,
        on_delete=models.CASCADE,
        related_name='epoch_history'
    )
    epoch_number = models.IntegerField()
    loss = models.FloatField()
    accuracy = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    val_loss = models.FloatField(null=True, blank=True)
    val_accuracy = models.FloatField(null=True, blank=True)
    learning_rate = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['epoch_number']
        unique_together = ['session', 'epoch_number']
        verbose_name = 'Эпоха обучения'
        verbose_name_plural = 'Эпохи обучения'