from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import MLModelForm, LayerForm
from .selectors import get_user_model, list_user_models
from .services import collect_layers, create_model


def _get_model(model_id, user):
    try:
        return get_user_model(model_id, user)
    except ObjectDoesNotExist as error:
        raise Http404 from error


@login_required
def model_list(request):
    return render(request, 'models/list.html', {'models': list_user_models(request.user)})


@login_required
def model_create(request):
    initial_layer = LayerForm(prefix='layer_0')
    form = MLModelForm(request.POST or None)
    layers = []
    layers_valid = True

    if request.method == 'POST':
        layers, layers_valid = collect_layers(request.POST, LayerForm)
        if form.is_valid() and layers_valid and layers:
            create_model(form=form, user=request.user, layers=layers)
            messages.success(request, 'Модель успешно создана')
            return redirect('model_list')
        if not layers:
            messages.error(request, 'Добавьте хотя бы один слой')
        elif not layers_valid:
            messages.error(request, 'Проверьте параметры слоёв')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')

    return render(request, 'models/create.html', {
        'form': form,
        'initial_layer': initial_layer,
    })


@login_required
def model_detail(request, pk):
    return render(request, 'models/detail.html', {'model': _get_model(pk, request.user)})


@login_required
@require_POST
def model_delete(request, pk):
    model = _get_model(pk, request.user)
    model.delete()
    messages.success(request, 'Модель удалена')
    return redirect('model_list')


@login_required
def model_train(request, pk):
    model = _get_model(pk, request.user)
    if request.method == 'POST':
        messages.info(request, 'Обучение запускается из раздела сессий обучения после выбора датасета.')
        return redirect('model_train', pk=pk)
    return render(request, 'models/train.html', {'model': model})


@login_required
def training_progress(request, pk):
    model = _get_model(pk, request.user)
    return JsonResponse({
        'status': model.get_status_display() if hasattr(model, 'get_status_display') else 'created',
        'log': getattr(model, 'training_log', ''),
        'accuracy': getattr(model, 'accuracy', None),
        'time': getattr(model, 'training_time', None),
    })
