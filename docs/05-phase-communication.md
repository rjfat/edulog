# Phase 5: Communication Features

## Objective
Implement announcements, messaging, and schedule management.

## Duration
3-4 days

## Tasks

### 5.1 Announcement Model
```python
# announcements/models.py
from django.db import models
from accounts.models import User

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    target_role = models.CharField(max_length=10, choices=[
        ('all', 'All'),
        ('student', 'Students'),
        ('teacher', 'Teachers'),
        ('parent', 'Parents'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 5.2 Message Model
```python
# messages/models.py
from django.db import models
from accounts.models import User

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 5.3 Schedule Model
```python
# schedule/models.py
from django.db import models
from courses.models import Course

class Schedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=[
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)
```

### 5.4 Views Implementation
- Announcement list/create/edit (admin/teacher)
- Message inbox/sent/compose
- Schedule view (weekly timetable)

### 5.5 Templates
```
templates/
├── announcements/
│   ├── announcement_list.html
│   └── announcement_form.html
├── messages/
│   ├── inbox.html
│   ├── sent.html
│   └── compose.html
└── schedule/
    └── timetable.html
```

## Deliverables
- [x] Announcement system
- [x] Messaging system
- [x] Schedule/Timetable
- [x] All related templates

## Next Phase
[Phase 6: Admin & Reports](./06-phase-admin-reports.md)
