from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import admin_required, staff_required, student_required

from .forms import CourseForm, EnrollmentForm
from .models import Course, Enrollment


def _can_manage(user, course):
    return user.is_admin or (user.is_teacher and course.teacher_id == user.pk)


@login_required
def course_list(request):
    user = request.user
    courses = Course.objects.select_related('teacher').annotate(student_count=Count('enrollments'))

    if user.is_teacher:
        courses = courses.filter(teacher=user)

    enrolled_ids = set()
    if user.is_student:
        enrolled_ids = set(
            Enrollment.objects.filter(student=user).values_list('course_id', flat=True)
        )
        for course in courses:
            course.is_enrolled = course.pk in enrolled_ids

    return render(request, 'courses/course_list.html', {'courses': courses})


@login_required
def course_detail(request, pk):
    course = get_object_or_404(
        Course.objects.select_related('teacher').annotate(student_count=Count('enrollments')),
        pk=pk,
    )
    user = request.user
    is_enrolled = user.is_student and course.enrollments.filter(student=user).exists()

    context = {
        'course': course,
        'can_manage': _can_manage(user, course),
        'is_enrolled': is_enrolled,
    }
    return render(request, 'courses/course_detail.html', context)


@staff_required
def course_create(request):
    form = CourseForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        course = form.save(commit=False)
        if request.user.is_teacher:
            course.teacher = request.user
        course.save()
        messages.success(request, f'{course.name} has been created.')
        return redirect('course_detail', pk=course.pk)

    return render(request, 'courses/course_form.html', {'form': form, 'course': None})


@staff_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if not _can_manage(request.user, course):
        messages.error(request, 'You do not have access to that page.')
        return redirect('course_detail', pk=course.pk)

    form = CourseForm(request.POST or None, instance=course, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{course.name} has been updated.')
        return redirect('course_detail', pk=course.pk)

    return render(request, 'courses/course_form.html', {'form': form, 'course': course})


@admin_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        name = course.name
        course.delete()
        messages.success(request, f'{name} has been deleted.')
        return redirect('course_list')

    return render(request, 'courses/course_confirm_delete.html', {'course': course})


@staff_required
def course_roster(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if not _can_manage(request.user, course):
        messages.error(request, 'You do not have access to that page.')
        return redirect('course_detail', pk=course.pk)

    form = EnrollmentForm(course=course)
    context = {
        'course': course,
        'enrollments': course.enrollments.select_related('student'),
        'form': form,
    }
    return render(request, 'courses/enrollment_list.html', context)


@staff_required
def course_enroll(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if not _can_manage(request.user, course):
        messages.error(request, 'You do not have access to that page.')
        return redirect('course_detail', pk=course.pk)

    form = EnrollmentForm(request.POST or None, course=course)
    if request.method == 'POST' and form.is_valid():
        student = form.cleaned_data['student']
        Enrollment.objects.create(student=student, course=course)
        messages.success(request, f'{student.display_name} has been enrolled in {course.code}.')
    else:
        messages.error(request, 'Choose a student to enroll.')

    return redirect('course_roster', pk=course.pk)


@staff_required
def course_unenroll(request, pk, student_pk):
    course = get_object_or_404(Course, pk=pk)
    if not _can_manage(request.user, course):
        messages.error(request, 'You do not have access to that page.')
        return redirect('course_detail', pk=course.pk)

    if request.method == 'POST':
        enrollment = get_object_or_404(Enrollment, course=course, student_id=student_pk)
        name = enrollment.student.display_name
        enrollment.delete()
        messages.success(request, f'{name} has been removed from {course.code}.')

    return redirect('course_roster', pk=course.pk)


@student_required
def course_join(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        _, created = Enrollment.objects.get_or_create(student=request.user, course=course)
        if created:
            messages.success(request, f'You are now enrolled in {course.code}.')
        else:
            messages.info(request, f'You are already enrolled in {course.code}.')

    return redirect('course_detail', pk=course.pk)


@student_required
def course_leave(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        Enrollment.objects.filter(student=request.user, course=course).delete()
        messages.success(request, f'You have left {course.code}.')

    return redirect('course_detail', pk=course.pk)
