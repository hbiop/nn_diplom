from .models import TrainingEpoch, TrainingSession


def get_user_session(session_id, user):
    return TrainingSession.objects.select_related('dataset', 'model').get(
        pk=session_id,
        user=user,
    )


def list_user_sessions(user):
    return TrainingSession.objects.filter(user=user).select_related(
        'dataset', 'model'
    ).order_by('-creation_date')


def get_epoch_history(session):
    return TrainingEpoch.objects.filter(session=session).order_by('epoch_number')
