from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import LoginForm, ProfileForm, RegistrationForm
from .models import Role, User

# Each role gets its own dashboard template; the shared view picks one.
DASHBOARD_TEMPLATES = {
    Role.ADMIN: 'accounts/dashboards/admin.html',
    Role.TEACHER: 'accounts/dashboards/teacher.html',
    Role.STUDENT: 'accounts/dashboards/student.html',
    Role.PARENT: 'accounts/dashboards/parent.html',
}


class EduLogLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().display_name}.')
        return super().form_valid(form)


class EduLogLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, 'You have been signed out.')
        return super().dispatch(request, *args, **kwargs)


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user, backend='apps.accounts.backends.UsernameOrEmailBackend')
        messages.success(request, f'Your account is ready. Welcome to EduLog, {user.first_name}.')
        return redirect('dashboard')

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard(request):
    template = DASHBOARD_TEMPLATES.get(request.user.role, 'accounts/dashboards/student.html')
    context = {}

    if request.user.is_admin:
        counts = User.objects.aggregate(
            total=Count('pk'),
            teachers=Count('pk', filter=Q(role=Role.TEACHER)),
            students=Count('pk', filter=Q(role=Role.STUDENT)),
            parents=Count('pk', filter=Q(role=Role.PARENT)),
        )
        context = {
            'user_count': counts['total'],
            'teacher_count': counts['teachers'],
            'student_count': counts['students'],
            'parent_count': counts['parents'],
        }

    return render(request, template, context)


@login_required
def profile(request):
    return render(request, 'accounts/profile.html')


@login_required
def profile_edit(request):
    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your profile has been updated.')
        return redirect('profile')

    return render(request, 'accounts/profile_edit.html', {'form': form})


class EduLogPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        messages.success(self.request, 'Your password has been changed.')
        return super().form_valid(form)


class EduLogPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.txt'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')


class EduLogPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class EduLogPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class EduLogPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'
