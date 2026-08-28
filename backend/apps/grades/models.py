from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.accounts.models import Role, User
from apps.courses.models import Course


class Grade(models.Model):
    GRADE_A_PLUS = 'A+'
    GRADE_A = 'A'
    GRADE_A_MINUS = 'A-'
    GRADE_B_PLUS = 'B+'
    GRADE_B = 'B'
    GRADE_B_MINUS = 'B-'
    GRADE_C_PLUS = 'C+'
    GRADE_C = 'C'
    GRADE_C_MINUS = 'C-'
    GRADE_D_PLUS = 'D+'
    GRADE_D = 'D'
    GRADE_D_MINUS = 'D-'
    GRADE_F = 'F'

    GRADE_CHOICES = [
        (GRADE_A_PLUS, 'A+'),
        (GRADE_A, 'A'),
        (GRADE_A_MINUS, 'A-'),
        (GRADE_B_PLUS, 'B+'),
        (GRADE_B, 'B'),
        (GRADE_B_MINUS, 'B-'),
        (GRADE_C_PLUS, 'C+'),
        (GRADE_C, 'C'),
        (GRADE_C_MINUS, 'C-'),
        (GRADE_D_PLUS, 'D+'),
        (GRADE_D, 'D'),
        (GRADE_D_MINUS, 'D-'),
        (GRADE_F, 'F'),
    ]

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='grades',
        limit_choices_to={'role': Role.STUDENT},
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='grades')
    assignment_name = models.CharField(max_length=200)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['course__code', 'student__last_name', 'student__first_name']
        unique_together = ('student', 'course', 'assignment_name')

    def __str__(self):
        return f'{self.student.display_name} - {self.assignment_name} ({self.grade})'

    @property
    def is_pass(self):
        return self.percentage >= 60
