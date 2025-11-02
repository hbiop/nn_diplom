from django.urls import path
from predict import views as predict_views
from predict.views import PredictionSessionDetailView, start_prediction_view

urlpatterns = [
    path('predictions/', predict_views.sessions_list, name='predict_sessions_list'),
    path('predictions/create', predict_views.create_session, name='create_session'),
    path('predictions/<int:pk>/', PredictionSessionDetailView.as_view(), name='prediction_detail'),
    path('predictions/<int:pk>/start/', start_prediction_view, name='start_prediction'),
]