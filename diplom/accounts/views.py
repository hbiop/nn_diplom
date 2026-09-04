from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import LoginForm, CustomUserForm, CustomUserCreationForm
from .selectors import get_user, list_users
from .services import save_user_form


def _get_user(user_id):
    try:
        return get_user(user_id)
    except ObjectDoesNotExist as error:
        raise Http404 from error


def login_view(request):
    form = LoginForm(data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('dataset_list')
    return render(request, 'login.html', {'form': form})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def user_detail(request, pk):
    return render(request, 'user_detail.html', {'custom_user': _get_user(pk)})


@login_required
def users_list(request):
    return render(request, 'user_list.html', {'users': list_users()})


@login_required
@user_passes_test(lambda user: user.is_staff)
def user_form(request, user_id=None):
    user = _get_user(user_id) if user_id else None
    form_class = CustomUserForm if user else CustomUserCreationForm
    form = form_class(request.POST or None, instance=user)

    if request.method == 'POST' and form.is_valid():
        save_user_form(form)
        return redirect('user_list')

    return render(request, 'user_form.html', {
        'form': form,
        'form_title': 'Редактирование пользователя' if user else 'Добавление нового пользователя',
        'user_id': user_id,
        'editing': user_id is not None,
    })
