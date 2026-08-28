from django import forms

from apps.accounts.forms import StyledFormMixin

from .models import Announcement


class AnnouncementForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'target_role']
        widgets = {'content': forms.Textarea()}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and not user.is_admin:
            # Teachers share news with everyone, students or other teachers.
            allowed = (
                Announcement.TARGET_ALL,
                Announcement.TARGET_STUDENT,
                Announcement.TARGET_TEACHER,
            )
            self.fields['target_role'].choices = [
                choice for choice in self.fields['target_role'].choices if choice[0] in allowed
            ]