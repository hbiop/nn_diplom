"""
URL configuration for diplom project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from datasets import views as datasets_views
from neural_network import views as neural_network_views

from predict import views as predict_views
from django.conf import settings
from django.conf.urls.static import static
from predict.views import PredictionSessionDetailView, start_prediction_view
from accounts import views as account_views

urlpatterns = [
    path('', datasets_views.redirect_to_dataset_list),
    path('user_list/', account_views.users_list, name='user_list'),
    path('users/add/', account_views.user_form, name='add_user'),
    path('users/<int:user_id>/edit/', account_views.user_form, name='edit_user'),
    path('user_detail/<int:pk>/', account_views.user_detail, name='user_detail'),
    #path('admin/register/', account_views.admin_register_view, name='admin_register'),
    path('admin/', admin.site.urls, name='admin'),
    path('upload/', datasets_views.upload_dataset, name='dataset_upload'),
    path('dataset/<int:pk>/', datasets_views.dataset_detail, name='dataset_detail'),
    path('datasets/', datasets_views.dataset_list, name='dataset_list'),
    path('datasets/<int:id>/delete/', datasets_views.delete_file, name='delete_file'),
    path('neural_network', neural_network_views.model_list, name='model_list'),
    path('neural_network/create/', neural_network_views.model_create, name='model_create'),
    path('neural_network/<int:pk>/', neural_network_views.model_detail, name='model_detail'),

    #learning
    path('learning/', include('learning.urls')),


    #predictions
    path('predictions/', predict_views.sessions_list, name='predict_sessions_list'),
    path('predictions/create', predict_views.create_session, name='create_session'),
    path('predictions/<int:pk>/', PredictionSessionDetailView.as_view(), name='prediction_detail'),
    path('predictions/<int:pk>/start/', start_prediction_view, name='start_prediction'),

    #accounts
    #path('register/', account_views.register_view, name='register'),
    path('login/', account_views.login_view, name='login'),
    path('logout/', account_views.logout_view, name='logout'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)