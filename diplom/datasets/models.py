import json
import os

from django.db import models
from django.urls import reverse
from django.conf import settings

# Create your models here.
class DataFile(models.Model):
    FILE_TYPES = (
        ('CSV', 'CSV'),
        ('XLSX', 'Excel'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='datasets'
    )

    title = models.CharField(max_length=255, verbose_name="Название набора")
    description = models.TextField(verbose_name="Описание", blank=True)
    file = models.FileField(upload_to='datasets/', verbose_name="Файл данных")
    file_type = models.CharField(max_length=5, choices=FILE_TYPES, verbose_name="Тип файла")
    file_size = models.PositiveIntegerField(verbose_name="Размер файла (байт)")
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        verbose_name = "Файл данных"
        verbose_name_plural = "Файлы данных"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Автоматическое определение типа файла и размера
        self.file_type = os.path.splitext(self.file.name)[1][1:].upper()
        self.file_size = self.file.size
        super().save(*args, **kwargs)

    def get_file_size_mb(self):
        return f"{self.file_size / (1024 * 1024):.2f} MB"

    def get_absolute_url(self):
        return reverse('dataset_detail', args=[str(self.id)])