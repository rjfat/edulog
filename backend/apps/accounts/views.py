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
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy

from apps.announcements.models import Announcement
from apps.attendance.models import Attendance
from apps.courses.models import Course, Enrollment
from apps.grades.models import Grade
from apps.messaging.models import Message
from apps.reports.audit import log_action

from .decorators import admin_required
from .forms import (
    LoginForm,
    ProfileForm,
    RegistrationForm,
    UserCreateForm,
    UserEditForm,
)
from .models import Role, User


def _visible_announcements(user):
    qs = Announcement.objects.select_related('author')
    if user.is_admin:
        return qs
    return qs.filter(
        Q(target_role__in=(Announcement.TARGET_ALL, user.role)) | Q(author=user)
    )


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
    context = {
        'announcements': _visible_announcements(request.user)[:3],
        'recent_messages': Message.objects.filter(receiver=request.user)
        .select_related('sender')[:3],
    }

    if request.user.is_admin:
        counts = User.objects.aggregate(
            total=Count('pk'),
            teachers=Count('pk', filter=Q(role=Role.TEACHER)),
            students=Count('pk', filter=Q(role=Role.STUDENT)),
            parents=Count('pk', filter=Q(role=Role.PARENT)),
        )
        from apps.reports.models import AuditLog

        context = {
            'user_count': counts['total'],
            'teacher_count': counts['teachers'],
            'student_count': counts['students'],
            'parent_count': counts['parents'],
            'course_count': Course.objects.count(),
            'enrollment_count': Enrollment.objects.count(),
            'grade_count': Grade.objects.count(),
            'recent_activity': AuditLog.recent(limit=8),
        }
    elif request.user.is_teacher:
        context = {
            'courses': Course.objects.filter(teacher=request.user)
            .annotate(student_count=Count('enrollments'))
            .order_by('code')[:5],
            'recent_grades': Grade.objects.filter(course__teacher=request.user)
            .select_related('student', 'course')
            .order_by('-created_at')[:5],
            'today_attendance': Attendance.objects.filter(course__teacher=request.user)
            .select_related('student', 'course')
            .order_by('-date', '-pk')[:5],
        }
    elif request.user.is_student:
        context = {
            'enrollments': Enrollment.objects.filter(student=request.user)
            .select_related('course', 'course__teacher')
            .order_by('course__code')[:5],
            'recent_grades': Grade.objects.filter(student=request.user)
            .select_related('course')
            .order_by('-created_at')[:5],
            'recent_attendance': Attendance.objects.filter(student=request.user)
            .select_related('course')
            .order_by('-date', '-pk')[:5],
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


def _user_queryset(request):
    users = User.objects.all()
    role = request.GET.get('role', '')
    query = request.GET.get('q', '').strip()
    if role in Role.values:
        users = users.filter(role=role)
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )
    return users


@admin_required
def user_list(request):
    if request.method == 'POST':
        return _user_list_bulk(request)

    role_counts = {
        row['role']: row['count'] for row in User.objects.values('role').annotate(count=Count('pk'))
    }
    page_obj = Paginator(_user_queryset(request).order_by('last_name', 'first_name').distinct(), 20).get_page(
        request.GET.get('page')
    )

    return render(request, 'admin/user_list.html', {
        'page_obj': page_obj,
        'role_counts': role_counts,
        'role_options': Role.choices,
        'filter_role': request.GET.get('role', ''),
        'filter_query': request.GET.get('q', ''),
    })


def _user_list_bulk(request):
    ids = [int(pk) for pk in request.POST.getlist('selected') if pk.isdigit()]
    action = request.POST.get('action', '')
    targets = User.objects.filter(pk__in=ids).exclude(pk=request.user.pk)
    count = targets.count()

    if action == 'activate':
        targets.update(is_active=True)
        messages.success(request, f'{count} account{"s" if count != 1 else ""} activated.')
    elif action == 'deactivate':
        targets.update(is_active=False)
        messages.success(request, f'{count} account{"s" if count != 1 else ""} deactivated.')
    elif action == 'delete':
        targets.delete()
        messages.success(request, f'{count} account{"s" if count != 1 else ""} deleted.')
    else:
        messages.error(request, 'Choose an action to apply.')

    return redirect('user_list')


@admin_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    context = {
        'profile_user': user,
        'enrollments': user.enrollments.select_related('course')[:10],
        'recent_grades': user.grades.select_related('course').order_by('-created_at')[:10],
        'recent_attendance': user.attendance.select_related('course').order_by('-date')[:10],
        'courses_taught': user.courses_taught.all()[:10],
    }
    if user.is_teacher:
        context['class_size'] = user.courses_taught.aggregate(total=Count('enrollments'))['total']
    return render(request, 'admin/user_detail.html', context)


@admin_required
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        log_action('user.created', f'{user.display_name} ({user.get_role_display()})')
        messages.success(request, f'Account for {user.display_name} has been created.')
        return redirect('user_detail', pk=user.pk)

    return render(request, 'admin/user_form.html', {'form': form, 'editing': False, 'profile_user': None})


@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserEditForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_action('user.updated', f'{user.display_name} ({user.get_role_display()})')
        messages.success(request, f'Account for {user.display_name} has been updated.')
        return redirect('user_detail', pk=user.pk)

    return render(request, 'admin/user_form.html', {'form': form, 'editing': True, 'profile_user': user})


@admin_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.pk == request.user.pk:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('user_detail', pk=user.pk)

    if request.method == 'POST':
        name = user.display_name
        user.delete()
        messages.success(request, f'Account for {name} has been deleted.')
        return redirect('user_list')

    return render(request, 'admin/user_confirm_delete.html', {'profile_user': user})
