from django import forms

from apps.accounts.forms import StyledFormMixin
from apps.accounts.models import User

from .models import Message


class MessageForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'subject', 'body']
        widgets = {'body': forms.Textarea()}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        recipients = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        if user is not None:
            recipients = recipients.exclude(pk=user.pk)
        self.fields['receiver'].queryset = recipients