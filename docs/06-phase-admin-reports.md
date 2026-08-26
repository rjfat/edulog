# Phase 6: Admin & Reports

## Objective
Implement admin dashboard, user management, audit logs, and reporting features.

## Duration
3-4 days

## Tasks

### 6.1 Audit Log Model
```python
# reports/models.py
from django.db import models
from accounts.models import User

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
```

### 6.2 Admin Dashboard
- System statistics (total users, courses, etc.)
- Recent activity
- Quick actions

### 6.3 User Management
- User list with filters
- Create/Edit/Delete users
- Bulk actions
- User details view

### 6.4 System Settings
- Site configuration
- Email settings
- Academic year settings

### 6.5 Reports
- Student progress reports
- Course performance reports
- Attendance reports
- Export to PDF/CSV

### 6.6 Templates
```
templates/admin/
├── dashboard.html
├── user_list.html
├── user_form.html
├── settings.html
└── audit_logs.html
templates/reports/
├── student_report.html
├── course_report.html
└── attendance_report.html
```

## Deliverables
- [x] Admin dashboard
- [x] User management CRUD
- [x] Audit logging
- [x] System settings
- [x] Report generation

## Next Phase
[Phase 7: Polish & Deployment](./07-phase-polish-deployment.md)
