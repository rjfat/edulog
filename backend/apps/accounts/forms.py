from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import Role, User


class StyledFormMixin:
    """Attach the shared input classes so templates stay free of widget markup."""

    error_css_class = 'has-error'
    required_css_class = 'is-required'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect)):
                continue
            css = 'select' if isinstance(widget, forms.Select) else 'input'
            existing = widget.attrs.get('class', '')
            widget.attrs['class'] = f'{existing} {css}'.strip()
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('rows', 3)


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = forms.CharField(
        label='Username or email',
        widget=forms.TextInput(attrs={'autocomplete': 'username', 'autofocus': True}),
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': 'That username/email and password do not match an account.',
    }


class RegistrationForm(StyledFormMixin, UserCreationForm):
    role = forms.ChoiceField(
        label='I am a',
        choices=[(Role.STUDENT, 'Student'), (Role.TEACHER, 'Teacher'), (Role.PARENT, 'Parent')],
        widget=forms.RadioSelect,
        initial=Role.STUDENT,
        help_text='Admin accounts are created by an existing administrator.',
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'role', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['username'].widget.attrs['autocomplete'] = 'username'
        self.fields['email'].widget.attrs['autocomplete'] = 'email'
        self.fields['phone'].widget.attrs['autocomplete'] = 'tel'
        self.fields['password1'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['password2'].widget.attrs['autocomplete'] = 'new-password'

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def clean_role(self):
        # Self-service signup must never mint an admin, whatever was posted.
        role = self.cleaned_data['role']
        if role == Role.ADMIN:
            raise ValidationError('Select a valid role.')
        return role


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'profile_picture']
        widgets = {'address': forms.Textarea()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        taken = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if taken.exists():
            raise ValidationError('An account with this email already exists.')
        return email
