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


def session_detail(request, pk):
    session = get_object_or_404(TrainingSession, pk=pk)
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

def create_session(request):
    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            training_session = form.save()
            return redirect('session_list')
    else:
        form = SessionForm()

    return render(request, "learning/upload_session.html", {"form": form})



def start_training_view(request, session_id):
    start_training(session_id)
    return JsonResponse({'status': 'Training started in background'})

def check_training_status(request, session_id):
    session = TrainingSession.objects.get(id=session_id)
    return JsonResponse({
        'status': session.status,
        'progress': session.progress,
        'current_epoch': session.current_epoch,
        'logs': session.logs.split('\n')[-10:]  # последние 10 строк логов
    })

def training_progress(request, session_id):
    """View для отображения страницы прогресса обучения"""
    session = get_object_or_404(TrainingSession, id=session_id)
    print("training progress func")
    return render(request, 'learning/training_progress.html', {
        'session': session,
    })

def training_progress_api(request, session_id):
    print("training progress api")
    session = TrainingSession.objects.get(id=session_id)

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


def cancel_training(request, session_id):
    print("training progress cancel")
    session = TrainingSession.objects.get(id=session_id)
    session.status = 'cancelled'
    session.save()
    return JsonResponse({'success': True})