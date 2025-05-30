import pickle
import threading

import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET

from predict.models import PredictSession

from predict.forms import PredictSessionForm

from predict.models import PredictionResult

from predict.tasks import PredictionThread


# Create your views here.
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

def predict(request, session_id):
    session = PredictSession.objects.get(id=session_id)
    if session.dataset.file_type == 'CSV':
        df = pd.read_csv(session.dataset.file.path)
    elif session.dataset.file_type == 'XLSX':
        df = pd.read_excel(session.dataset.file.path)
    preprocessor = pickle.load(session.model.preprocessor)
    data = preprocessor.preprocess_data_for_predict(df)
    neural_network = pickle.load(session.model.neural_network)
    output = neural_network.predict(data)
    prediction_result = PredictionResult.objects.create(
            session=session,
            input_data=data.tolist(),
            prediction=output.tolist()
        )
    result = PredictionResult.objects.get(session=session.id)
    context = {
            'session': session,
            'input_data': result.input_data,
            'output_data': result.prediction
        }


def prediction_detail_view(request, pk):
    print("here")
    predict_session = get_object_or_404(PredictSession, pk=pk)

    if predict_session.status == 'running':
        print("here 2")
        active_threads = [t for t in threading.enumerate() if
                          isinstance(t, PredictionThread) and t.session.id == predict_session.id]
        if not active_threads:
            predict_session.refresh_from_db()
            if predict_session.status == 'running':
                predict_session.status = 'failed'
                predict_session.logs = "Поток выполнения был прерван"
                predict_session.save()

    results = predict_session.results.all()[:50]
    summary = predict_session.get_results_summary()

    context = {
        'object': predict_session,
        'results': results,
        'summary': summary,
    }

    return render(request, 'predictions/prediction_detail.html', context)


@require_GET
def check_prediction_status(request, pk):
    """API endpoint для проверки статуса (используется AJAX)"""
    predict_session = get_object_or_404(PredictSession, pk=pk)

    # Проверяем активные потоки для этой сессии
    active_threads = [t for t in threading.enumerate() if
                      isinstance(t, PredictionThread) and t.session.id == predict_session.id]

    return JsonResponse({
        'status': predict_session.status,
        'progress': predict_session.progress,
        'is_active': len(active_threads) > 0,
        'logs': predict_session.logs,
    })