from django import forms

from apps.accounts.forms import StyledFormMixin
from apps.accounts.models import Role, User

from .models import Course


class CourseForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'code', 'description', 'teacher']
        widgets = {'description': forms.Textarea()}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = User.objects.filter(role=Role.TEACHER)
        if user is not None and user.is_teacher:
            # A teacher's own courses are always taught by them; no need to ask.
            del self.fields['teacher']


class EnrollmentForm(StyledFormMixin, forms.Form):
    student = forms.ModelChoiceField(
        label='Student',
        queryset=User.objects.none(),
        empty_label='Select a student',
    )

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        enrolled_ids = course.enrollments.values_list('student_id', flat=True)
        self.fields['student'].queryset = (
            User.objects.filter(role=Role.STUDENT).exclude(pk__in=enrolled_ids)
        )
