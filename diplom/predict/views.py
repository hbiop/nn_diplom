import pickle
import threading

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET
from django.views.generic import DetailView

from predict.models import PredictSession

from predict.forms import PredictSessionForm

from predict.models import PredictionResult

from predict.tasks import PredictionThread

from predict.tasks import start_prediction


@login_required
def sessions_list(request):
    sessions = PredictSession.objects.all().order_by('-creation_date')
    return render(request, 'predictions/list.html', {'sessions': sessions})

def create_session(request):
    if request.method == 'POST':
        form = PredictSessionForm(request.POST)
        if form.is_valid():
            training_session = form.save()
            return redirect('predict_sessions_list')
    else:
        form = PredictSessionForm()

    return render(request, "predictions/upload_session.html", {"form": form})


class PredictionSessionDetailView(DetailView):
    model = PredictSession
    template_name = 'predictions/prediction_detail.html'
    context_object_name = 'session'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.object

        # Собираем статистику по результатам
        if session.status == 'completed':
            context['results_summary'] = session.get_results_summary()

        # Форматируем прогресс для отображения
        context['progress_percent'] = int(session.progress)
        context['progress_width'] = f"{session.progress}%"

        # Разбиваем логи на строки для лучшего отображения
        context['logs_lines'] = session.logs.split('\n') if session.logs else []

        return context


def start_prediction_view(request, pk):
    session = get_object_or_404(PredictSession, pk=pk)

    # Запускаем только если сессия не выполняется
    if session.status != 'running':
        start_prediction(session.id)
        return JsonResponse({
            'status': 'started',
            'message': f'Предсказание для сессии "{session.title}" запущено'
        })
    else:
        return JsonResponse({
            'status': 'already_running',
            'message': 'Предсказание уже выполняется'
        })