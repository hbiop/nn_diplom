def create_prediction_session(*, form, user):
    session = form.save(commit=False)
    session.user = user
    session.save()
    return session


def start_prediction_if_idle(session, task):
    if session.status == 'running':
        return False
    task(session.id)
    return True


def build_prediction_context(session):
    context = {
        'progress_percent': int(session.progress),
        'progress_width': f'{session.progress}%',
        'logs_lines': session.logs.split('\n') if session.logs else [],
    }
    if session.status == 'completed':
        context['results_summary'] = session.get_results_summary()
    return context
