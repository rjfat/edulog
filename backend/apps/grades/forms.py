from django import forms

from apps.accounts.forms import StyledFormMixin
from apps.accounts.models import Role, User
from apps.courses.models import Course

from .models import Grade

GRADE_LABELS = ', '.join(label for _, label in Grade.GRADE_CHOICES)


def manageable_courses(user):
    courses = Course.objects.all()
    if user.is_teacher:
        courses = courses.filter(teacher=user)
    return courses


def enrolled_students(course):
    enrolled_ids = course.enrollments.values_list('student_id', flat=True)
    return User.objects.filter(role=Role.STUDENT, pk__in=enrolled_ids).order_by('last_name', 'first_name')


class GradeForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['student', 'course', 'assignment_name', 'grade', 'percentage', 'comments']
        widgets = {'comments': forms.Textarea(),
                   'percentage': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': '0.01'})}

    def __init__(self, *args, user=None, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['course'].queryset = manageable_courses(user)
        if course is not None:
            self.fields['course'].initial = course
            self.fields['student'].queryset = enrolled_students(course)
