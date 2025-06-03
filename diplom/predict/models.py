import numpy as np
import pandas as pd
from django.db import models

from datasets.models import DataFile
from django.urls import reverse

from learning.models import TrainingSession
from django.utils import timezone

# Create your models here.

class PredictSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('running', 'Выполняется'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
    ]
    progress = models.FloatField(default=0)
    title = models.CharField(max_length=255, default="Новая сессия предсказаний")
    dataset = models.ForeignKey(DataFile, on_delete=models.CASCADE)
    model = models.ForeignKey(TrainingSession, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    logs = models.TextField(blank=True)
    results_file = models.FileField(upload_to='predictions/', null=True, blank=True)

    def get_absolute_url(self):
        return reverse('prediction_detail', kwargs={'pk': self.pk})

    def make_predictions(self):
        try:
            self.status = 'running'
            self.save()

            training_session = self.model
            nn = training_session.load_neural_network()
            preprocessor = training_session.load_preprocessor()

            if nn is None or preprocessor is None:
                raise ValueError("Модель или препроцессор не загружены")

            df = pd.read_csv(self.dataset.file.path)
            X_preprocessed = preprocessor.preprocess_data_for_predict(df)

            predictions = nn.predict(X_preprocessed)

            results = []
            for i, row in df.iterrows():
                prediction = predictions[i]
                predicted_class = preprocessor.get_predicted_label(prediction)

                result = PredictionResult(
                    session=self,
                    input_data=row.to_dict(),
                    prediction={
                        'raw': prediction.tolist(),
                        'class': predicted_class,
                        'confidence': float(np.max(prediction))
                    }
                )
                results.append(result)

            PredictionResult.objects.bulk_create(results)

            results_df = df.copy()
            results_df['prediction'] = [preprocessor.get_predicted_label(p) for p in predictions]
            results_df['confidence'] = [np.max(p) for p in predictions]

            output_path = f'media/predictions/session_{self.pk}_results.csv'
            results_df.to_csv(output_path, index=False)
            self.results_file.name = output_path[6:]  # Убираем 'media/' из пути

            self.status = 'completed'
            self.save()

            return True
        except Exception as e:
            self.status = 'failed'
            self.logs = str(e)
            self.save()
            return False

    def get_results_summary(self):
        from django.db.models import Count
        return self.results.values('prediction__class').annotate(
            count=Count('id')
        ).order_by('-count')

    def __str__(self):
        return f"{self.title} ({self.creation_date.strftime('%Y-%m-%d')})"


class PredictionResult(models.Model):
    session = models.ForeignKey(PredictSession, on_delete=models.CASCADE, related_name='results')
    input_data = models.JSONField(help_text="Исходные данные для предсказания")
    prediction = models.JSONField(help_text="Результаты предсказания")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def get_prediction_details(self):
        pred = self.prediction
        return {
            'predicted_class': pred.get('class', 'N/A'),
            'confidence': f"{pred.get('confidence', 0) * 100:.2f}%",
            'raw': pred.get('raw', [])
        }

    def __str__(self):
        return f"Предсказание #{self.id} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"