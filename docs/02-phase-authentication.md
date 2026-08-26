# Phase 2: Authentication & User Management

## Objective
Implement user authentication, registration, and role-based access control.

## Duration
3-4 days

## Tasks

### 2.1 Custom User Model
```python
# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 2.2 Authentication Views
- Login page (HTML form)
- Registration page with role selection
- Password reset functionality
- Logout functionality

### 2.3 Role-Based Access Control
```python
# accounts/decorators.py
from functools import wraps
from django.shortcuts import redirect

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### 2.4 User Profile Management
- Profile view page
- Edit profile functionality
- Password change

### 2.5 Templates Structure
```
templates/
├── base.html
├── accounts/
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   └── dashboard.html
└── components/
    ├── navbar.html
    ├── sidebar.html
    └── footer.html
```

## Deliverables
- [x] Custom User model
- [x] Login/Registration system
- [x] Role-based decorators
- [x] User profile management
- [x] Base templates

## Next Phase
[Phase 3: Course Management](./03-phase-courses.md)
