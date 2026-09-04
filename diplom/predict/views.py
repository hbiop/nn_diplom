from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from .forms import PredictSessionForm
from .models import PredictSession
from .selectors import get_user_prediction_session, list_user_prediction_sessions
from .services import build_prediction_context, create_prediction_session, start_prediction_if_idle
from .tasks import start_prediction


def _get_session(session_id, user):
    try:
        return get_user_prediction_session(session_id, user)
    except ObjectDoesNotExist as error:
        raise Http404 from error


@login_required
def sessions_list(request):
    sessions = list_user_prediction_sessions(request.user)
    return render(request, 'predictions/list.html', {'sessions': sessions})


@login_required
def create_session(request):
    form = PredictSessionForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        create_prediction_session(form=form, user=request.user)
        return redirect('predict_sessions_list')
    return render(request, 'predictions/upload_session.html', {'form': form})


class PredictionSessionDetailView(LoginRequiredMixin, DetailView):
    login_url = 'login'
    model = PredictSession
    template_name = 'predictions/prediction_detail.html'
    context_object_name = 'session'

    def get_object(self, queryset=None):
        return _get_session(self.kwargs['pk'], self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_prediction_context(self.object))
        return context


@login_required
@require_POST
def delete_prediction_session(request, pk):
    session = _get_session(pk, request.user)
    if session.status == 'running':
        messages.error(request, 'Нельзя удалить активную сессию предсказаний')
        return redirect('prediction_detail', pk=pk)
    result_file = session.results_file
    session.delete()
    if result_file:
        result_file.delete(save=False)
    return redirect('predict_sessions_list')


@login_required
@require_POST
def start_prediction_view(request, pk):
    session = _get_session(pk, request.user)
    started = start_prediction_if_idle(session, start_prediction)
    if started:
        return JsonResponse({
            'status': 'started',
            'message': f'Предсказание для сессии "{session.title}" запущено',
        })
    return JsonResponse({
        'status': 'already_running',
        'message': 'Предсказание уже выполняется',
    })
