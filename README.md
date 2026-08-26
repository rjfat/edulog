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
