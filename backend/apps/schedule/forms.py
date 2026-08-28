from django import forms

from apps.accounts.forms import StyledFormMixin
from apps.courses.models import Course

from .models import Schedule


class ScheduleForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['course', 'day_of_week', 'start_time', 'end_time', 'room']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'placeholder': 'e.g. 15:30'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            courses = Course.objects.all()
            if user.is_teacher:
                courses = courses.filter(teacher=user)
            self.fields['course'].queryset = courses