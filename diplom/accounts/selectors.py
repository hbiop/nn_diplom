from .models import CustomUser


def get_user(user_id):
    return CustomUser.objects.get(pk=user_id)


def list_users():
    return CustomUser.objects.all().order_by('-date_joined')
