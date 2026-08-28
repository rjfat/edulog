import csv

from django.contrib import messages
from django.db.models import Avg, Count, Max, Min, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import admin_required, staff_required
from apps.accounts.models import Role, User
from apps.attendance.models import Attendance
from apps.courses.models import Course
from apps.grades.models import Grade

from .audit import log_action
from .forms import CourseSelectForm, SchoolSettingsForm, StudentSelectForm
from .models import AuditLog, SchoolSettings


def _csv_response(filename):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response, csv.writer(response)


def _manageable_courses(user):
    courses = Course.objects.all()
    if user.is_teacher:
        courses = courses.filter(teacher=user)
    return courses


@staff_required
def report_index(request):
    return render(request, 'reports/report_index.html')


@admin_required
def audit_logs(request):
    from django.core.paginator import Paginator

    page_obj = Paginator(
        AuditLog.objects.select_related('user').order_by('-created_at').all(), 50
    ).get_page(request.GET.get('page'))
    return render(request, 'admin/audit_logs.html', {'page_obj': page_obj})


@admin_required
def settings_view(request):
    settings = SchoolSettings.load()
    form = SchoolSettingsForm(request.POST or None, instance=settings)
    if request.method == 'POST' and form.is_valid():
        settings = form.save(commit=False)
        settings.updated_by = request.user
        settings.save()
        log_action(
            'settings.updated',
            f'School name: {form.cleaned_data["school_name"]}; '
            f'Academic year: {form.cleaned_data["academic_year"] or "—"}; '
            f'Term: {form.cleaned_data["term_label"] or "—"}',
        )
        messages.success(request, 'System settings have been updated.')
        return redirect('settings')

    return render(request, 'admin/settings.html', {'form': form, 'settings': settings})


@staff_required
def student_report(request):
    user = request.user
    student = None
    if 'student' in request.GET:
        student = get_object_or_404(User, pk=request.GET.get('student'), role=Role.STUDENT)

    if request.GET.get('format') == 'csv' and student is not None:
        return _student_report_csv(student)

    grades = Grade.objects.none()
    attendance = Attendance.objects.none()
    stats = None
    by_course = []

    if student is not None:
        grades = Grade.objects.filter(student=student).select_related('course')
        attendance = Attendance.objects.filter(student=student).select_related('course')
        stats = grades.aggregate(
            count=Count('pk'),
            average=Avg('percentage'),
            highest=Max('percentage'),
            lowest=Min('percentage'),
        )
        total = stats['count'] or 1
        stats['pass_rate'] = round(
            (grades.filter(percentage__gte=60).count() / total) * 100 if stats['count'] else 0
        )

        courses = grades.values('course_id', 'course__code', 'course__name').order_by('course__code')
        for row in courses:
            course_grades = grades.filter(course_id=row['course_id'])
            row['average'] = course_grades.aggregate(average=Avg('percentage'))['average']
            row['grade_count'] = course_grades.count()
            row['attendance'] = attendance.filter(course_id=row['course_id']).aggregate(
                present=Count('pk', filter=Q(status=Attendance.STATUS_PRESENT)),
                absent=Count('pk', filter=Q(status=Attendance.STATUS_ABSENT)),
                late=Count('pk', filter=Q(status=Attendance.STATUS_LATE)),
            )
            by_course.append(row)

    overall_attendance = attendance.aggregate(
        present=Count('pk', filter=Q(status=Attendance.STATUS_PRESENT)),
        absent=Count('pk', filter=Q(status=Attendance.STATUS_ABSENT)),
        late=Count('pk', filter=Q(status=Attendance.STATUS_LATE)),
    )

    context = {
        'form': StudentSelectForm(request.GET or None),
        'student': student,
        'grades': grades,
        'stats': stats,
        'by_course': by_course,
        'overall_attendance': overall_attendance,
    }
    return render(request, 'reports/student_report.html', context)


def _student_report_csv(student):
    response, writer = _csv_response(f'student-{student.username}.csv')
    writer.writerow(['Course', 'Assignment', 'Grade', 'Percentage', 'Comments', 'Date'])
    grades = Grade.objects.filter(student=student).select_related('course').order_by('course__code')
    for grade in grades:
        writer.writerow([
            grade.course.code,
            grade.assignment_name,
            grade.grade,
            float(grade.percentage),
            grade.comments,
            grade.created_at.strftime('%Y-%m-%d'),
        ])
    return response


@staff_required
def course_report(request):
    user = request.user
    course = None
    if 'course' in request.GET:
        course = get_object_or_404(_manageable_courses(user), pk=request.GET.get('course'))

    if request.GET.get('format') == 'csv' and course is not None:
        return _course_report_csv(course)

    context = {'form': CourseSelectForm(request.GET or None, user=user), 'course': course}
    if course is None:
        return render(request, 'reports/course_report.html', context)

    distribution = _distribution(course)
    attendance = course.attendance.aggregate(
        present=Count('pk', filter=Q(status=Attendance.STATUS_PRESENT)),
        absent=Count('pk', filter=Q(status=Attendance.STATUS_ABSENT)),
        late=Count('pk', filter=Q(status=Attendance.STATUS_LATE)),
    )
    context.update({
        'rows': _class_rows(course),
        'distribution': distribution,
        'attendance': attendance,
        'class_average': course.grades.aggregate(average=Avg('percentage'))['average'],
    })
    return render(request, 'reports/course_report.html', context)


def _class_rows(course):
    """Per-student grade summary for a course, in aggregate queries."""
    return (
        Grade.objects.filter(course=course)
        .values('student_id', 'student__first_name', 'student__last_name')
        .annotate(
            count=Count('pk'),
            average=Avg('percentage'),
            highest=Max('percentage'),
            pass_count=Count('pk', filter=Q(percentage__gte=60)),
        )
        .order_by('student__last_name', 'student__first_name')
    )


def _distribution(course):
    buckets = [('A', '90 – 100', Q(percentage__gte=90)),
               ('B', '80 – 89', Q(percentage__gte=80, percentage__lt=90)),
               ('C', '70 – 79', Q(percentage__gte=70, percentage__lt=80)),
               ('D', '60 – 69', Q(percentage__gte=60, percentage__lt=70)),
               ('F', 'Below 60', Q(percentage__lt=60))]
    grades = Grade.objects.filter(course=course)
    total = grades.count() or 1
    distribution = []
    for letter, label, q in buckets:
        n = grades.filter(q).count()
        distribution.append({
            'letter': letter,
            'label': label,
            'count': n,
            'percent': round((n / total) * 100),
        })
    return distribution


def _course_report_csv(course):
    response, writer = _csv_response(f'{course.code}-report.csv')
    writer.writerow(['Student', 'Assignments', 'Average %', 'Highest %', 'Passing', 'Pass rate %'])
    for record in _class_rows(course):
        name = f"{record['student__first_name']} {record['student__last_name']}".strip()
        average = record['average']
        writer.writerow([
            name,
            record['count'],
            round(float(average), 2) if average is not None else '',
            round(float(record['highest']), 2) if record['highest'] is not None else '',
            record['pass_count'],
            round((record['pass_count'] / record['count']) * 100) if record['count'] else 0,
        ])
    return response


@staff_required
def attendance_report(request):
    user = request.user
    course = None
    if 'course' in request.GET:
        course = get_object_or_404(_manageable_courses(user), pk=request.GET.get('course'))

    if request.GET.get('format') == 'csv' and course is not None:
        return _attendance_report_csv(course)

    context = {'form': CourseSelectForm(request.GET or None, user=user), 'course': course}
    if course is None:
        return render(request, 'reports/attendance_report.html', context)

    records = (
        course.attendance.values(
            'student_id', 'student__first_name', 'student__last_name'
        )
        .annotate(
            present=Count('pk', filter=Q(status=Attendance.STATUS_PRESENT)),
            absent=Count('pk', filter=Q(status=Attendance.STATUS_ABSENT)),
            late=Count('pk', filter=Q(status=Attendance.STATUS_LATE)),
            total=Count('pk'),
        )
        .order_by('student__last_name', 'student__first_name')
    )
    for record in records:
        record['rate'] = round((record['present'] / record['total']) * 100) if record['total'] else 0

    overall = course.attendance.aggregate(
        present=Count('pk', filter=Q(status=Attendance.STATUS_PRESENT)),
        absent=Count('pk', filter=Q(status=Attendance.STATUS_ABSENT)),
        late=Count('pk', filter=Q(status=Attendance.STATUS_LATE)),
    )
    overall['rate'] = round(
        (overall['present'] / sum(overall.values())) * 100
    ) if any(overall.values()) else 0

    context.update({
        'rows': records,
        'overall': overall,
        'enrolled': course.enrollments.count(),
        'dates_with_records': course.attendance.values('date').distinct().count(),
    })
    return render(request, 'reports/attendance_report.html', context)


def _attendance_report_csv(course):
    response, writer = _csv_response(f'{course.code}-attendance.csv')
    writer.writerow(['Student', 'Present', 'Absent', 'Late', 'Total', 'Attendance rate %'])
    records = (
        course.attendance.values('student_id', 'student__first_name', 'student__last_name')
        .annotate(
            present=Count('pk', filter=Q(status=Attendance.STATUS_PRESENT)),
            absent=Count('pk', filter=Q(status=Attendance.STATUS_ABSENT)),
            late=Count('pk', filter=Q(status=Attendance.STATUS_LATE)),
            total=Count('pk'),
        )
        .order_by('student__last_name', 'student__first_name')
    )
    for record in records:
        name = f"{record['student__first_name']} {record['student__last_name']}".strip()
        writer.writerow([
            name,
            record['present'],
            record['absent'],
            record['late'],
            record['total'],
            round((record['present'] / record['total']) * 100) if record['total'] else 0,
        ])
    return response