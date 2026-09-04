from .models import DataFile


def get_user_dataset(dataset_id, user):
    return DataFile.objects.get(pk=dataset_id, user=user)


def list_user_datasets(user):
    return DataFile.objects.filter(user=user).order_by('-upload_date')
