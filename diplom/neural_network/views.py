from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import MLModel
from .forms import MLModelForm
import json


def model_list(request):
    models = MLModel.objects.all().order_by('-creation_date')
    return render(request, 'models/list.html', {'models': models})


def model_create(request):
    if request.method == 'POST':
        form = MLModelForm(request.POST)
        try:
            json.loads(request.POST['parameters'])
            if form.is_valid():
                form.save()
                messages.success(request, 'Модель успешно создана')
                return redirect('model_list')
            else:
                messages.error(request, form.errors)
        except json.JSONDecodeError as e:
            print(f"error {e}")
            messages.error(request, 'Ошибка в формате JSON параметров')
        except Exception as e:
            messages.error(request, f'Произошла ошибка: {str(e)}')
    else:
        form = MLModelForm()

    return render(request, 'models/create.html', {'form': form})


def model_detail(request, pk):
    model = get_object_or_404(MLModel, pk=pk)
    return render(request, 'models/detail.html', {'model': model})




def model_train(request, pk):
    model = get_object_or_404(MLModel, pk=pk)

    if request.method == 'POST':
        # Начало обучения
        model.status = 'training'
        model.save()

        # Запуск обучения в отдельном потоке (упрощенная версия)
        from threading import Thread
        Thread(target=train_model, args=(model,)).start()

        return redirect('model_train', pk=pk)

    return render(request, 'models/train.html', {'model': model})


def train_model(model):
    try:
        # Имитация процесса обучения
        start_time = time.time()

        # Здесь должна быть реальная логика обучения
        for epoch in range(1, 6):
            time.sleep(2)  # Имитация обучения
            model.training_log = f"Epoch {epoch}/5 completed\n"
            model.save()

        model.accuracy = 0.92  # Пример метрики
        model.training_time = time.time() - start_time
        model.status = 'completed'
        model.training_log += "\nОбучение успешно завершено!"

    except Exception as e:
        model.status = 'failed'
        model.training_log = f"Ошибка: {str(e)}"

    model.save()


def training_progress(request, pk):
    model = get_object_or_404(MLModel, pk=pk)
    return JsonResponse({
        'status': model.get_status_display(),
        'log': model.training_log,
        'accuracy': model.accuracy,
        'time': model.training_time
    })