from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import DataFileForm
from .selectors import get_user_dataset, list_user_datasets
from .services import create_dataset, delete_dataset, read_dataset_preview


def _get_dataset(dataset_id, user):
    try:
        return get_user_dataset(dataset_id, user)
    except ObjectDoesNotExist as error:
        raise Http404 from error


@login_required
def upload_dataset(request):
    form = DataFileForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        try:
            data_file = create_dataset(form=form, user=request.user)
            messages.success(request, 'Файл успешно загружен и обработан')
            return redirect('dataset_detail', pk=data_file.pk)
        except Exception as error:
            messages.error(request, f'Ошибка обработки файла: {error}')

    return render(request, 'datasets/upload.html', {'form': form})


@login_required
@require_POST
def delete_file(request, id):
    delete_dataset(_get_dataset(id, request.user))
    return redirect('dataset_list')


@login_required
def dataset_detail(request, pk):
    data_file = _get_dataset(pk, request.user)
    context = {'data_file': data_file}
    try:
        context.update(read_dataset_preview(data_file))
    except Exception as error:
        messages.error(request, f'Ошибка чтения файла: {error}')

    return render(request, 'datasets/detail.html', context)


@login_required
def dataset_list(request):
    return render(request, 'datasets/list.html', {
        'datasets': list_user_datasets(request.user),
    })


def redirect_to_dataset_list(request):
    return redirect('dataset_list')
