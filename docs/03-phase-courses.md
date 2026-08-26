# Phase 3: Course Management

## Objective
Implement course creation, enrollment, and management features.

## Duration
2-3 days

## Tasks

### 3.1 Course Model
```python
# courses/models.py
from django.db import models
from accounts.models import User

class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student', 'course')
```

### 3.2 Course Views
- Course list (for teachers: their courses, for students: enrolled courses)
- Course detail page
- Create/Edit course (teacher/admin only)
- Delete course (admin only)

### 3.3 Enrollment System
- Enroll student in course
- Unenroll student from course
- View enrolled students

### 3.4 Course Templates
```
templates/courses/
├── course_list.html
├── course_detail.html
├── course_form.html
└── enrollment_list.html
```

## Deliverables
- [x] Course model
- [x] Enrollment model
- [x] CRUD views for courses
- [x] Enrollment management
- [x] Course templates

## Next Phase
[Phase 4: Grades & Attendance](./04-phase-grades-attendance.md)
