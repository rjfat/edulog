from django import forms

from apps.accounts.forms import StyledFormMixin
from apps.accounts.models import Role, User
from apps.courses.models import Course

from .models import SchoolSettings


class StudentSelectForm(StyledFormMixin, forms.Form):
    student = forms.ModelChoiceField(
        label='Student',
        queryset=User.objects.filter(role=Role.STUDENT).order_by('last_name', 'first_name'),
        empty_label='Choose a student',
    )


class CourseSelectForm(StyledFormMixin, forms.Form):
    course = forms.ModelChoiceField(
        label='Course',
        queryset=Course.objects.none(),
        empty_label='Choose a course',
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        courses = Course.objects.all()
        if user is not None and user.is_teacher:
            courses = courses.filter(teacher=user)
        self.fields['course'].queryset = courses


class SchoolSettingsForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = SchoolSettings
        fields = ['school_name', 'academic_year', 'term_label', 'contact_email']