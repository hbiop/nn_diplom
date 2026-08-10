import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import SessionForm
from .models import TrainingSession, TrainingEpoch
from .tasks import start_training
from neural_network.models import MLModel
from .models import TrainingSession
from datasets.models import DataFile

@login_required
def sessions_list(request):
    sessions = TrainingSession.objects.filter(user=request.user).order_by('-creation_date')
    return render(request, 'learning/list.html', {'sessions': sessions})

@login_required
def session_detail(request, pk):
    session = get_object_or_404(TrainingSession, pk=pk, user=request.user)
    data_file = session.dataset
    neural_network = session.model

    context = {
        'session': session,
        'data_file': data_file,
        'model': neural_network
    }

    try:
        if data_file.file_type == 'CSV':
            df = pd.read_csv(data_file.file.path)
        elif data_file.file_type == 'XLSX':
            df = pd.read_excel(data_file.file.path)

        context.update({
            'columns': df.columns.tolist(),
            'rows': df.to_dict('records')[:100]
        })
    except Exception as e:
        messages.error(request, f'Ошибка чтения файла: {str(e)}')

    return render(request, 'learning/detail.html', context)

@login_required
def create_session(request):
    if request.method == 'POST':
        form = SessionForm(request.POST, user=request.user)
        if form.is_valid():
            training_session = form.save(commit=False)
            training_session.user = request.user
            training_session.save()
            return redirect('session_list')
    else:
        form = SessionForm(user=request.user)

    return render(request, "learning/upload_session.html", {"form": form})



@login_required
def start_training_view(request, session_id):
    get_object_or_404(TrainingSession, id=session_id, user=request.user)
    task = start_training(session_id)
    return JsonResponse({
        'status': 'queued',
        'task_id': task.id,
        'message': 'Обучение поставлено в очередь Celery',
    })

@login_required
def check_training_status(request, session_id):
    session = get_object_or_404(TrainingSession, id=session_id, user=request.user)
    return JsonResponse({
        'status': session.status,
        'progress': session.progress,
        'current_epoch': session.current_epoch,
        'logs': session.logs.split('\n')[-10:]  # последние 10 строк логов
    })

@login_required
def training_progress(request, session_id):
    """View для отображения страницы прогресса обучения"""
    session = get_object_or_404(TrainingSession, id=session_id, user=request.user)
    print("training progress func")
    return render(request, 'learning/training_progress.html', {
        'session': session,
    })

@login_required
def training_progress_api(request, session_id):
    print("training progress api")
    session = get_object_or_404(TrainingSession, id=session_id, user=request.user)

    epoch_history = list(TrainingEpoch.objects.filter(session=session))

    return JsonResponse({
        'status': session.status,
        'progress': session.progress,
        'logs': session.logs,
        'epoch_history': [
            {
                'epoch_number': e.epoch_number,
                'loss': e.loss,
                'accuracy': e.accuracy
            } for e in epoch_history
        ]
    })


@login_required
@require_POST
def cancel_training(request, session_id):
    session = get_object_or_404(TrainingSession, id=session_id, user=request.user)
    session.status = 'cancelled'
    session.save()
    return JsonResponse({'success': True})