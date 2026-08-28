from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import staff_required
from apps.courses.models import Course

from .forms import AttendanceMarkForm, AttendanceRowForm, manageable_courses
from .models import Attendance


def _course_scope(user, pk=None):
    """Resolve a course a staff member may work with (or None)."""
    if pk is None:
        return None
    options = Course.objects.all()
    if user.is_teacher:
        options = options.filter(teacher=user)
    return get_object_or_404(options, pk=pk)


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


@login_required
def attendance_list(request):
    user = request.user
    records = Attendance.objects.select_related('student', 'course', 'course__teacher')

    if user.is_student:
        records = records.filter(student=user)
    elif user.is_teacher:
        records = records.filter(course__teacher=user)

    course_pk = request.GET.get('course')
    course = None
    if course_pk:
        course = _course_scope(user, course_pk)
        records = records.filter(course=course)

    summary = (
        records.order_by('course__code').values('course__code', 'course__name')
        .annotate(
            present=Count('pk', filter=Q(status=Attendance.STATUS_PRESENT)),
            absent=Count('pk', filter=Q(status=Attendance.STATUS_ABSENT)),
            late=Count('pk', filter=Q(status=Attendance.STATUS_LATE)),
            total=Count('pk'),
        ).order_by('course__code')
    )

    context = {
        'records': records,
        'course': course,
        'summary': summary,
        'course_options': manageable_courses(user) if user.is_teacher or user.is_admin else None,
    }
    return render(request, 'attendance/attendance_list.html', context)


@staff_required
def attendance_mark(request):
    user = request.user
    RowFormSet = formset_factory(AttendanceRowForm, extra=0)

    if request.method == 'POST' and 'save_attendance' in request.POST:
        course = _course_scope(user, request.POST.get('course'))
        mark_date = _parse_date(request.POST.get('date'))
        students = list(course.enrollments.select_related('student').order_by('student__last_name'))
        formset = RowFormSet(request.POST, prefix='rows')
        if mark_date and students and formset.is_valid():
            for enrollment, row_form in zip(students, formset.forms):
                data = row_form.cleaned_data
                Attendance.objects.update_or_create(
                    student=enrollment.student,
                    course=course,
                    date=mark_date,
                    defaults={'status': data['status'], 'notes': data['notes']},
                )
            messages.success(request, f'Attendance for {course.code} on {mark_date} has been saved.')
            return redirect('attendance_list')
        return render(request, 'attendance/attendance_mark.html', {
            'mark_form': AttendanceMarkForm(user=user),
            'course': course,
            'date': mark_date,
            'mark_rows': list(zip([e.student for e in students], formset.forms)),
        })

    mark_form = AttendanceMarkForm(
        request.POST or None,
        user=user,
        initial={'date': request.GET.get('date')},
    )
    course = None
    date = None
    students = []
    formset = None

    if request.method == 'POST' and mark_form.is_valid():
        course = mark_form.cleaned_data['course']
        date = mark_form.cleaned_data['date']
    elif request.method == 'GET' and request.GET.get('course'):
        course = _course_scope(user, request.GET.get('course'))
        date = _parse_date(request.GET.get('date'))

    if course and date:
        students = list(course.enrollments.select_related('student').order_by('student__last_name'))
        existing = {
            r['student_id']: r
            for r in Attendance.objects.filter(course=course, date=date).values(
                'student_id', 'status', 'notes'
            )
        }
        initial = [
            {
                'status': existing.get(s.pk, {}).get('status', Attendance.STATUS_PRESENT),
                'notes': existing.get(s.pk, {}).get('notes', ''),
            }
            for s in students
        ]
        formset = RowFormSet(initial=initial, prefix='rows')

    context = {
        'mark_form': mark_form,
        'course': course,
        'date': date,
        'mark_rows': list(zip(students, formset.forms)) if formset else None,
        'rows_formset': formset,
    }
    return render(request, 'attendance/attendance_mark.html', context)


@staff_required
def attendance_report(request):
    user = request.user
    course_pk = request.GET.get('course')
    course = _course_scope(user, course_pk) if course_pk else None

    records = Attendance.objects.select_related('student')
    if course is not None:
        records = records.filter(course=course)
    elif user.is_teacher:
        records = records.filter(course__teacher=user)

    per_student = (
        records.values('student_id', 'student__first_name', 'student__last_name', 'student__username')
        .annotate(
            present=Count('pk', filter=Q(status=Attendance.STATUS_PRESENT)),
            absent=Count('pk', filter=Q(status=Attendance.STATUS_ABSENT)),
            late=Count('pk', filter=Q(status=Attendance.STATUS_LATE)),
            total=Count('pk'),
        ).order_by('student__last_name', 'student__first_name')
    )
    for row in per_student:
        row['present_rate'] = round((row['present'] / row['total']) * 100) if row['total'] else 0

    overall = records.aggregate(
        total=Count('pk'),
        present=Count('pk', filter=Q(status=Attendance.STATUS_PRESENT)),
        absent=Count('pk', filter=Q(status=Attendance.STATUS_ABSENT)),
        late=Count('pk', filter=Q(status=Attendance.STATUS_LATE)),
    )
    overall['present_rate'] = round(
        (overall['present'] / overall['total']) * 100
    ) if overall['total'] else 0

    context = {
        'course': course,
        'per_student': per_student,
        'overall': overall,
        'course_options': manageable_courses(user),
    }
    return render(request, 'attendance/attendance_report.html', context)
