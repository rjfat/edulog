# EduLog

Educational management system for students, teachers, parents and administrators.
See [`docs/00-project-overview.md`](docs/00-project-overview.md) for the full plan.

## Stack

Django 5.2 · PostgreSQL 16 · HTML/CSS/vanilla JS

## Setup

```bash
# 1. Virtual environment
python -m venv venv
source venv/Scripts/activate    # Windows (Git Bash); use venv/bin/activate on Linux/macOS

# 2. Dependencies
pip install -r requirements.txt

# 3. Environment
cp .env.example .env            # then edit DJANGO_SECRET_KEY and the DB_* values

# 4. Database
createdb edulog_db              # requires a running PostgreSQL server
cd backend
python manage.py migrate

# 5. Admin account
python manage.py createsuperuser

# 6. Run
python manage.py runserver
```

The app is then at http://127.0.0.1:8000/ and the Django admin at
http://127.0.0.1:8000/admin/.

### Developing without PostgreSQL

Set `DB_ENGINE=sqlite` in `.env` to use a local `backend/db.sqlite3` file
instead. Everything else works the same; switch back before testing anything
database-specific.

## Layout

```
edulog/
├── backend/
│   ├── manage.py
│   ├── config/          # settings, root urlconf, wsgi/asgi
│   ├── apps/            # accounts, courses, grades, attendance,
│   │                    # announcements, schedule, messaging, reports
│   ├── templates/       # HTML templates
│   └── media/           # user uploads (git-ignored)
├── frontend/            # css/, js/, images/ served as static files
├── docs/                # project plan and phase documents
├── requirements.txt
└── .env.example
```

## Authentication

Everyone signs in through `/accounts/login/` with either their **username or
email address**. Roles are `admin`, `teacher`, `student` and `parent`; the
dashboard at `/accounts/dashboard/` renders a different template per role.
Self-service signup can only create teacher, student or parent accounts -
admins are made in the Django admin.

| URL | Purpose |
|-----|---------|
| `/accounts/login/` | Sign in |
| `/accounts/register/` | Create an account |
| `/accounts/dashboard/` | Role-specific dashboard |
| `/accounts/profile/` | View profile |
| `/accounts/profile/edit/` | Edit profile |
| `/accounts/password/change/` | Change password |
| `/accounts/password/reset/` | Request a reset link |

Password-reset mail prints to the console until `DJANGO_EMAIL_BACKEND` points
at a real SMTP backend.

Restrict a view to certain roles with the decorators in
`apps/accounts/decorators.py`:

```python
from apps.accounts.decorators import role_required, teacher_required

@teacher_required
def gradebook(request): ...

@role_required('admin', 'teacher')
def roster(request): ...
```

## Design system

The UI follows `design-system/edulog/MASTER.md` - Swiss/minimal, Lexend +
Source Sans 3, indigo primary with an orange accent. Tokens live at the top of
`frontend/css/main.css`; use the CSS variables rather than raw hex values.

## Common commands

Run from `backend/`:

| Command | Purpose |
|---------|---------|
| `python manage.py runserver` | Start the dev server |
| `python manage.py makemigrations` | Create migrations from model changes |
| `python manage.py migrate` | Apply migrations |
| `python manage.py createsuperuser` | Create an admin account |
| `python manage.py check` | Validate project configuration |
| `python manage.py test` | Run the test suite |
