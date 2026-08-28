from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max, Min, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import staff_required

from .forms import GradeForm, manageable_courses
from .models import Grade


def _can_manage(user, course):
    return user.is_admin or (user.is_teacher and course.teacher_id == user.pk)


def _resolve_course(user, course_pk):
    if course_pk is None:
        return None
    return get_object_or_404(manageable_courses(user), pk=course_pk)


def _grade_queryset(user, course=None):
    grades = Grade.objects.select_related('student', 'course', 'course__teacher')
    if user.is_student:
        grades = grades.filter(student=user)
    elif user.is_teacher:
        grades = grades.filter(course__teacher=user)
    if course is not None:
        grades = grades.filter(course=course)
    return grades


@login_required
def grade_list(request):
    user = request.user
    course_pk = request.GET.get('course')
    course = _resolve_course(user, course_pk) if course_pk else None

    grades = _grade_queryset(user, course)

    course_options = manageable_courses(user) if user.is_staff or user.is_teacher else None

    context = {
        'grades': grades,
        'course': course,
        'course_options': course_options,
    }
    return render(request, 'grades/grade_list.html', context)


@staff_required
def grade_add(request):
    course_pk = (
        request.POST.get('course') if request.method == 'POST' else request.GET.get('course')
    )
    course = None
    if course_pk:
        course = manageable_courses(request.user).filter(pk=course_pk).first()
        if course is None:
            messages.error(request, 'You do not have access to that page.')
            return redirect('grade_list')

    form = GradeForm(request.POST or None, user=request.user, course=course)
    if request.method == 'POST' and form.is_valid():
        grade = form.save()
        messages.success(
            request,
            f"Posted {grade.grade} for {grade.assignment_name} on {grade.course.code}.",
        )
        return redirect('grade_list')

    return render(request, 'grades/grade_form.html', {'form': form, 'grade': None})


@staff_required
def grade_edit(request, pk):
    grade = get_object_or_404(Grade, pk=pk)
    if not _can_manage(request.user, grade.course):
        messages.error(request, 'You do not have access to that page.')
        return redirect('grade_list')

    form = GradeForm(request.POST or None, instance=grade, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Updated {grade.assignment_name} for {grade.student.display_name}.')
        return redirect('grade_list')

    return render(request, 'grades/grade_form.html', {'form': form, 'grade': grade})


@staff_required
def grade_delete(request, pk):
    grade = get_object_or_404(Grade, pk=pk)
    if not _can_manage(request.user, grade.course):
        messages.error(request, 'You do not have access to that page.')
        return redirect('grade_list')

    if request.method == 'POST':
        description = str(grade)
        grade.delete()
        messages.success(request, f'Deleted {description}.')
        return redirect('grade_list')

    return render(request, 'grades/grade_confirm_delete.html', {'grade': grade})


@staff_required
def grade_report(request):
    user = request.user
    course_pk = request.GET.get('course')
    course = _resolve_course(user, course_pk) if course_pk else None

    grades = Grade.objects.filter(course=course) if course else _grade_queryset(user)

    stats = grades.aggregate(
        count=Count('pk'),
        average=Avg('percentage'),
        highest=Max('percentage'),
        lowest=Min('percentage'),
    )

    distribution = []
    buckets = [('A', '90 – 100', Q(percentage__gte=90)),
               ('B', '80 – 89', Q(percentage__gte=80, percentage__lt=90)),
               ('C', '70 – 79', Q(percentage__gte=70, percentage__lt=80)),
               ('D', '60 – 69', Q(percentage__gte=60, percentage__lt=70)),
               ('F', 'Below 60', Q(percentage__lt=60))]
    total = stats['count'] or 1
    for letter, label, q in buckets:
        n = grades.filter(q).count()
        distribution.append({
            'letter': letter,
            'label': label,
            'count': n,
            'percent': round((n / total) * 100),
        })

    course_options = manageable_courses(user)

    context = {
        'course': course,
        'course_options': course_options,
        'stats': stats,
        'distribution': distribution,
        'pass_rate': round(
            (grades.filter(percentage__gte=60).count() / total) * 100 if stats['count'] else 0
        ),
    }
    return render(request, 'grades/grade_report.html', context)
