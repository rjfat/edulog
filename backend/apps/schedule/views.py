from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import staff_required
from apps.courses.models import Course

from .forms import ScheduleForm
from .models import Schedule


def _can_manage(user, course):
    return user.is_admin or (user.is_teacher and course.teacher_id == user.pk)


@login_required
def timetable(request):
    user = request.user
    courses = Course.objects.all()
    if user.is_student:
        courses = courses.filter(enrollments__student=user)
    elif user.is_teacher:
        courses = courses.filter(teacher=user)

    sessions = (
        Schedule.objects.filter(course__in=courses)
        .select_related('course', 'course__teacher')
    )

    grouped = defaultdict(list)
    for session in sessions:
        grouped[session.day_of_week].append(session)

    days = [
        {
            'day': day,
            'label': label,
            'items': grouped.get(day, []),
        }
        for day, label in Schedule.DAY_CHOICES
    ]

    context = {
        'days': days,
        'has_sessions': bool(sessions),
        'can_manage': user.is_admin or user.is_teacher,
    }
    return render(request, 'schedule/timetable.html', context)


@staff_required
def schedule_create(request):
    form = ScheduleForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        schedule = form.save()
        messages.success(
            request,
            f'{schedule.course.code} on {schedule.get_day_of_week_display()} has been scheduled.',
        )
        return redirect('timetable')

    return render(request, 'schedule/schedule_form.html', {'form': form, 'schedule': None})


@staff_required
def schedule_edit(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if not _can_manage(request.user, schedule.course):
        messages.error(request, 'You do not have access to that page.')
        return redirect('timetable')

    form = ScheduleForm(request.POST or None, instance=schedule, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(
            request,
            f'{schedule.course.code} on {schedule.get_day_of_week_display()} has been updated.',
        )
        return redirect('timetable')

    return render(request, 'schedule/schedule_form.html', {'form': form, 'schedule': schedule})


@staff_required
def schedule_delete(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if not _can_manage(request.user, schedule.course):
        messages.error(request, 'You do not have access to that page.')
        return redirect('timetable')

    if request.method == 'POST':
        description = str(schedule)
        schedule.delete()
        messages.success(request, f'{description} has been removed.')
        return redirect('timetable')

    return render(request, 'schedule/schedule_confirm_delete.html', {'schedule': schedule})