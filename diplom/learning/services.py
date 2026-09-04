from .models import TrainingSession


def create_training_session(*, form, user):
    session = form.save(commit=False)
    session.user = user
    session.save()
    return session


def queue_training(session_id, task):
    return task(session_id)


def cancel_training(session):
    session.status = 'cancelled'
    session.save(update_fields=['status'])
    return session


def serialize_training_progress(session, epoch_history):
    return {
        'status': session.status,
        'progress': session.progress,
        'logs': session.logs,
        'epoch_history': [
            {
                'epoch_number': epoch.epoch_number,
                'loss': epoch.loss,
                'accuracy': epoch.accuracy,
            }
            for epoch in epoch_history
        ],
    }
