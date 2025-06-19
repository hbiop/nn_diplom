import time

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import MLModel
from .forms import MLModelForm, LayerForm
import json

@login_required
def model_list(request):
    models = MLModel.objects.filter(user=request.user).order_by('-creation_date')
    return render(request, 'models/list.html', {'models': models})


def model_create(request):
    if request.method == 'POST':
        form = MLModelForm(request.POST)
        layers = []
        layers_valid = True

        layer_fields = [k for k in request.POST if k.startswith('layer_') and '-units' in k]
        layer_indices = sorted({int(k.split('_')[1].split('-')[0]) for k in layer_fields})

        for i in layer_indices:
            prefix = f'layer_{i}'
            layer_form = LayerForm({
                f'{prefix}-units': request.POST.get(f'{prefix}-units'),
                f'{prefix}-activation': request.POST.get(f'{prefix}-activation')
            }, prefix=prefix)

            if layer_form.is_valid():
                layers.append({
                    'size': layer_form.cleaned_data['units'],
                    'activation': layer_form.cleaned_data['activation']
                })
            else:
                layers_valid = False

        if form.is_valid() and layers_valid and layers:
            ml_model = form.save(commit=False)
            ml_model.parameters = {'layers': layers}
            ml_model.user = request.user
            ml_model.save()

            messages.success(request, 'Модель успешно создана')
            return redirect('model_list')
        else:
            if not layers:
                messages.error(request, 'Добавьте хотя бы один слой')
            elif not layers_valid:
                messages.error(request, 'Проверьте параметры слоёв')
            else:
                messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = MLModelForm()
        initial_layer = LayerForm(prefix='layer_0')

    return render(request, 'models/create.html', {
        'form': form,
        'initial_layer': initial_layer,
    })


def model_detail(request, pk):
    model = get_object_or_404(MLModel, pk=pk)
    return render(request, 'models/detail.html', {'model': model})




def model_train(request, pk):
    model = get_object_or_404(MLModel, pk=pk)

    if request.method == 'POST':
        model.status = 'training'
        model.save()
        from threading import Thread
        Thread(target=train_model, args=(model,)).start()

        return redirect('model_train', pk=pk)

    return render(request, 'models/train.html', {'model': model})


# def train_model(model):
#     try:
#         start_time = time.time()
#
#         for epoch in range(1, 6):
#             time.sleep(2)  # Имитация обучения
#             model.training_log = f"Epoch {epoch}/5 completed\n"
#             model.save()
#
#         model.accuracy = 0.92  # Пример метрики
#         model.training_time = time.time() - start_time
#         model.status = 'completed'
#         model.training_log += "\nОбучение успешно завершено!"
#
#     except Exception as e:
#         model.status = 'failed'
#         model.training_log = f"Ошибка: {str(e)}"
#
#     model.save()


def training_progress(request, pk):
    model = get_object_or_404(MLModel, pk=pk)
    return JsonResponse({
        'status': model.get_status_display(),
        'log': model.training_log,
        'accuracy': model.accuracy,
        'time': model.training_time
    })