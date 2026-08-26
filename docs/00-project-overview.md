# EduLog - Educational Management System

## Project Overview

EduLog is a comprehensive educational management system designed to streamline communication and administration between students, teachers, parents, and administrators.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| Backend | Django 5.x (Python) |
| Database | PostgreSQL 16 |
| Web Server | Nginx (Production) |
| WSGI | Gunicorn (Production) |

## User Roles

| Role | Description |
|------|-------------|
| **Admin** | Full system access, user management, system settings |
| **Teacher** | Course management, grade attendance, messaging |
| **Student** | View grades, attendance, schedules, messaging |
| **Parent** | View child's progress, grades, attendance, messaging |

## Core Features

1. **Authentication System** - Login, registration, role-based access
2. **Course Management** - Create, edit, delete courses
3. **Grade Management** - Track and manage student grades
4. **Attendance Tracking** - Record and view attendance
5. **Announcements** - System-wide announcements
6. **Schedule/Timetable** - Class schedules and timetable
7. **Messaging System** - Communication between users
8. **Reports & Analytics** - Generate reports and statistics

## Admin Features

1. **User Management** - CRUD operations for all users
2. **System Settings** - Configure system parameters
3. **Audit Logs** - Track system changes
4. **Dashboard** - Overview of system metrics

## Project Structure

```
edulog/
├── docs/                    # Documentation
├── backend/                 # Django project
│   ├── config/             # Django settings
│   ├── apps/               # Django apps
│   │   ├── accounts/       # User management
│   │   ├── courses/        # Course management
│   │   ├── grades/         # Grade management
│   │   ├── attendance/     # Attendance tracking
│   │   ├── announcements/  # Announcements
│   │   ├── schedule/       # Timetable
│   │   ├── messaging/      # Messaging system
│   │   └── reports/        # Reports & analytics
│   ├── templates/          # HTML templates
│   └── static/             # Static files (CSS, JS, images)
├── frontend/               # Static frontend assets
├── requirements/           # Python dependencies
├── .env.example           # Environment variables template
└── docker-compose.yml     # Docker setup (optional)
```

## Database Schema Overview

### Users Table (Extended Django User)
- id, email, password, role (admin/teacher/student/parent)
- first_name, last_name, phone, address
- profile_picture, created_at, updated_at

### Courses Table
- id, name, code, description
- teacher_id, created_at

### Enrollments Table
- id, student_id, course_id, enrolled_at

### Grades Table
- id, student_id, course_id, assignment_name
- grade, percentage, comments, created_at

### Attendance Table
- id, student_id, course_id, date
- status (present/absent/late), notes

### Announcements Table
- id, title, content, author_id
- target_role, created_at

### Schedules Table
- id, course_id, day_of_week
- start_time, end_time, room

### Messages Table
- id, sender_id, receiver_id
- subject, body, read, created_at

### Audit Logs Table
- id, user_id, action, details
- ip_address, created_at

## Development Phases

See individual phase documents for detailed implementation plans:

1. [Phase 1: Project Setup](./01-phase-project-setup.md)
2. [Phase 2: Authentication & Users](./02-phase-authentication.md)
3. [Phase 3: Course Management](./03-phase-courses.md)
4. [Phase 4: Grades & Attendance](./04-phase-grades-attendance.md)
5. [Phase 5: Communication Features](./05-phase-communication.md)
6. [Phase 6: Admin & Reports](./06-phase-admin-reports.md)
7. [Phase 7: Polish & Deployment](./07-phase-polish-deployment.md)
8. [Future Plans](./08-future-plans.md)

## Getting Started

```bash
# Clone and setup
git clone <repository-url>
cd edulog

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
createdb edulog_db
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```
