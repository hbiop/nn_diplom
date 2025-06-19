from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.template.loader import render_to_string
from django.urls import reverse

from .forms import LoginForm, CustomUserForm
from .models import CustomUser

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dataset_list')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def user_detail(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    return render(request, 'user_detail.html', {'custom_user': user})


@login_required
def users_list(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'user_list.html', {'users': users})


@login_required
@user_passes_test(lambda u: u.is_staff)
def user_form(request, user_id=None):
    if user_id:
        user = get_object_or_404(CustomUser, pk=user_id)
        print(user)
        form_title = "Редактирование пользователя"
    else:
        user = None
        form_title = "Добавление нового пользователя"

    if request.method == 'POST':
        form = CustomUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = CustomUserForm(instance=user)

    return render(request, 'user_form.html', {
        'form': form,
        'form_title': form_title,
        'user_id': user_id,
        'editing': user_id is not None
    })