from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import SessionForm
from .selectors import get_epoch_history, get_user_session, list_user_sessions
from .services import (
    cancel_training as cancel_training_service,
    create_training_session,
    serialize_training_progress,
)
from .tasks import start_training


def _get_session(session_id, user):
    try:
        return get_user_session(session_id, user)
    except ObjectDoesNotExist as error:
        raise Http404 from error


@login_required
def sessions_list(request):
    sessions = list_user_sessions(request.user)
    return render(request, 'learning/list.html', {'sessions': sessions})


@login_required
def session_detail(request, pk):
    session = _get_session(pk, request.user)
    context = {
        'session': session,
        'data_file': session.dataset,
        'model': session.model,
    }

    from datasets.services import read_dataset_preview

    try:
        context.update(read_dataset_preview(session.dataset))
    except Exception as error:
        messages.error(request, f'Ошибка чтения файла: {error}')

    return render(request, 'learning/detail.html', context)


@login_required
def create_session(request):
    form = SessionForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        create_training_session(form=form, user=request.user)
        return redirect('session_list')

    return render(request, 'learning/upload_session.html', {'form': form})


@login_required
def start_training_view(request, session_id):
    _get_session(session_id, request.user)
    task = start_training(session_id)
    return JsonResponse({
        'status': 'queued',
        'task_id': task.id,
        'message': 'Обучение поставлено в очередь Celery',
    })


@login_required
def check_training_status(request, session_id):
    session = _get_session(session_id, request.user)
    return JsonResponse({
        'status': session.status,
        'progress': session.progress,
        'current_epoch': session.current_epoch,
        'logs': session.logs.split('\n')[-10:],
    })


@login_required
def training_progress(request, session_id):
    session = _get_session(session_id, request.user)
    return render(request, 'learning/training_progress.html', {'session': session})


@login_required
def training_progress_api(request, session_id):
    session = _get_session(session_id, request.user)
    payload = serialize_training_progress(session, get_epoch_history(session))
    return JsonResponse(payload)


@login_required
@require_POST
def cancel_training(request, session_id):
    session = _get_session(session_id, request.user)
    cancel_training_service(session)
    return JsonResponse({'success': True})
