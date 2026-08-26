# Phase 4: Grades & Attendance

## Objective
Implement grade tracking and attendance management features.

## Duration
3-4 days

## Tasks

### 4.1 Grade Model
```python
# grades/models.py
from django.db import models
from accounts.models import User
from courses.models import Course

class Grade(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grades')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='grades')
    assignment_name = models.CharField(max_length=200)
    grade = models.CharField(max_length=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    GRADE_CHOICES = (
        ('A+', 'A+'), ('A', 'A'), ('A-', 'A-'),
        ('B+', 'B+'), ('B', 'B'), ('B-', 'B-'),
        ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'),
        ('D+', 'D+'), ('D', 'D'), ('D-', 'D-'),
        ('F', 'F'),
    )
```

### 4.2 Attendance Model
```python
# attendance/models.py
from django.db import models
from accounts.models import User
from courses.models import Course

class Attendance(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student', 'course', 'date')
```

### 4.3 Grade Views
- Add grade (teacher only)
- View grades (student: own grades, teacher: course grades)
- Edit/Delete grade (teacher only)
- Grade statistics

### 4.4 Attendance Views
- Mark attendance (teacher only)
- View attendance (student: own, teacher: course)
- Attendance report

### 4.5 Templates
```
templates/
├── grades/
│   ├── grade_list.html
│   ├── grade_form.html
│   └── grade_report.html
└── attendance/
    ├── attendance_mark.html
    ├── attendance_list.html
    └── attendance_report.html
```

## Deliverables
- [x] Grade model
- [x] Attendance model
- [x] Grade CRUD views
- [x] Attendance management
- [x] Report views

## Next Phase
[Phase 5: Communication Features](./05-phase-communication.md)
