from .models import PredictSession


def get_user_prediction_session(session_id, user):
    return PredictSession.objects.select_related('dataset', 'model').get(
        pk=session_id,
        user=user,
    )


def list_user_prediction_sessions(user):
    return PredictSession.objects.filter(user=user).select_related(
        'dataset', 'model'
    ).order_by('-creation_date')
