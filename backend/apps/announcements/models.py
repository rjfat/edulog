from django.db import models

from apps.accounts.models import User


class Announcement(models.Model):
    TARGET_ALL = 'all'
    TARGET_STUDENT = 'student'
    TARGET_TEACHER = 'teacher'
    TARGET_PARENT = 'parent'

    TARGET_CHOICES = [
        (TARGET_ALL, 'Everyone'),
        (TARGET_STUDENT, 'Students'),
        (TARGET_TEACHER, 'Teachers'),
        (TARGET_PARENT, 'Parents'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    target_role = models.CharField(max_length=10, choices=TARGET_CHOICES, default=TARGET_ALL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title