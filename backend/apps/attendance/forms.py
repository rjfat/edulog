from django import forms

from apps.accounts.forms import StyledFormMixin
from apps.courses.models import Course

from .models import Attendance


def manageable_courses(user):
    courses = Course.objects.all()
    if user.is_teacher:
        courses = courses.filter(teacher=user)
    return courses


class AttendanceMarkForm(StyledFormMixin, forms.Form):
    course = forms.ModelChoiceField(
        label='Course',
        queryset=Course.objects.none(),
        empty_label='Select a course',
    )
    date = forms.DateField(
        label='Date',
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='The class date you are recording attendance for.',
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['course'].queryset = manageable_courses(user)


class AttendanceRowForm(StyledFormMixin, forms.Form):
    status = forms.ChoiceField(
        label='Status',
        choices=Attendance.STATUS_CHOICES,
        widget=forms.Select,
    )
    notes = forms.CharField(
        label='Notes',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Optional'}),
    )
