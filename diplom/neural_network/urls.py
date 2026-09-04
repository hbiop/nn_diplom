from django.urls import path

from neural_network import views as neural_network_views

urlpatterns = [
    path('', neural_network_views.model_list, name='model_list'),
    path('create/', neural_network_views.model_create, name='model_create'),
    path('<int:pk>/', neural_network_views.model_detail, name='model_detail'),
    path('<int:pk>/delete/', neural_network_views.model_delete, name='model_delete'),
]