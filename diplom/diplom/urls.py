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

from neural_network import views as neural_network_views

from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views
from datasets import views as datasets_views
urlpatterns = [
    path('', datasets_views.redirect_to_dataset_list),
    #datasets
    path('datasets/', include('datasets.urls')),

    path('user_list/', account_views.users_list, name='user_list'),
    path('users/add/', account_views.user_form, name='add_user'),
    path('users/<int:user_id>/edit/', account_views.user_form, name='edit_user'),
    path('user_detail/<int:pk>/', account_views.user_detail, name='user_detail'),
    #path('admin/register/', account_views.admin_register_view, name='admin_register'),
    path('admin/', admin.site.urls, name='admin'),


    path('neural_network', neural_network_views.model_list, name='model_list'),
    path('neural_network/create/', neural_network_views.model_create, name='model_create'),
    path('neural_network/<int:pk>/', neural_network_views.model_detail, name='model_detail'),

    #learning
    path('learning/', include('learning.urls')),


    #predictions
    path('predicting/', include('predict.urls')),

    #accounts
    #path('register/', account_views.register_view, name='register'),
    path('datasets/login/', account_views.login_view, name='login'),
    path('logout/', account_views.logout_view, name='logout'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)