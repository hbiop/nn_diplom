import pickle

import pandas as pd
from django.shortcuts import render, redirect

from predict.models import PredictSession

from predict.forms import PredictSessionForm

from predict.models import PredictionResult


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