from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    TEACHER = 'teacher', 'Teacher'
    STUDENT = 'student', 'Student'
    PARENT = 'parent', 'Parent'


class User(AbstractUser):
    """EduLog user.

    Everyone signs in through this one model; `role` decides what they see.
    Username is kept as the login field, but email is required and unique so
    the email backend in `backends.py` can resolve it too.
    """

    email = models.EmailField('email address', unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    REQUIRED_FIELDS = ['email']

    class Meta:
        ordering = ['first_name', 'last_name', 'username']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def initials(self):
        first = (self.first_name or self.username or '?')[:1]
        last = (self.last_name or '')[:1]
        return (first + last).upper()

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_teacher(self):
        return self.role == Role.TEACHER

    @property
    def is_student(self):
        return self.role == Role.STUDENT

    @property
    def is_parent(self):
        return self.role == Role.PARENT
