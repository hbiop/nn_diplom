
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


@login_required
def model_create(request):
    initial_layer = LayerForm(prefix='layer_0')
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

    return render(request, 'models/create.html', {
        'form': form,
        'initial_layer': initial_layer,
    })


@login_required
def model_detail(request, pk):
    model = get_object_or_404(MLModel, pk=pk, user=request.user)
    return render(request, 'models/detail.html', {'model': model})




@login_required
def model_train(request, pk):
    model = get_object_or_404(MLModel, pk=pk, user=request.user)

    if request.method == 'POST':
        messages.info(
            request,
            'Обучение запускается из раздела сессий обучения после выбора датасета.'
        )
        return redirect('model_train', pk=pk)

    return render(request, 'models/train.html', {'model': model})



@login_required
def training_progress(request, pk):
    model = get_object_or_404(MLModel, pk=pk, user=request.user)
    return JsonResponse({
        'status': model.get_status_display(),
        'log': model.training_log,
        'accuracy': model.accuracy,
        'time': model.training_time
    })