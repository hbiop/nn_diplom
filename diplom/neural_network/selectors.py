from .models import MLModel


def get_user_model(model_id, user):
    return MLModel.objects.get(pk=model_id, user=user)


def list_user_models(user):
    return MLModel.objects.filter(user=user).order_by('-creation_date')
