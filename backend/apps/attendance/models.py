from django.db import models

from apps.accounts.models import Role, User
from apps.courses.models import Course


class Attendance(models.Model):
    STATUS_PRESENT = 'present'
    STATUS_ABSENT = 'absent'
    STATUS_LATE = 'late'

    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
        (STATUS_LATE, 'Late'),
    ]

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendance',
        limit_choices_to={'role': Role.STUDENT},
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'student__last_name', 'student__first_name']
        unique_together = ('student', 'course', 'date')

    def __str__(self):
        return f'{self.student.display_name} - {self.get_status_display()} on {self.date}'
