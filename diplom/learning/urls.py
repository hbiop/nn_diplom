from django.urls import path
from learning import views as learning_views

urlpatterns = [
    path('sessions/', learning_views.sessions_list, name='session_list'),
    path('sessions/create', learning_views.create_session, name='create_session_list'),
    path('session_detail/<int:pk>/', learning_views.session_detail, name='session_detail'),
    path('start_training/<int:session_id>/', learning_views.start_training_view, name='start_training'),
    path('training/<int:session_id>/', learning_views.training_progress, name='training_progress'),
    path('api/training-progress/<int:session_id>/', learning_views.training_progress_api, name='training_progress_api'),
    path('api/cancel-training/<int:session_id>/', learning_views.cancel_training, name='cancel_training'),
]