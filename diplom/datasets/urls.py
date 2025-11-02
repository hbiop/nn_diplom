from django.urls import path
from datasets import views as datasets_views

urlpatterns = [
    path('', datasets_views.redirect_to_dataset_list),
    path('upload/', datasets_views.upload_dataset, name='dataset_upload'),
    path('dataset/<int:pk>/', datasets_views.dataset_detail, name='dataset_detail'),
    path('datasets/', datasets_views.dataset_list, name='dataset_list'),
    path('datasets/<int:id>/delete/', datasets_views.delete_file, name='delete_file'),
]