# Phase 1: Project Setup

## Objective
Set up the Django project structure, PostgreSQL database, and development environment.

## Duration
1-2 days

## Tasks

### 1.1 Initialize Django Project
- Create Django project structure
- Configure project settings for PostgreSQL
- Set up virtual environment

### 1.2 Database Configuration
- Install PostgreSQL dependencies
- Configure database connection in settings.py
- Create .env file for environment variables

### 1.3 Project Structure Setup
```
edulog/
├── backend/
│   ├── manage.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── apps/
│       ├── __init__.py
│       ├── accounts/
│       ├── courses/
│       ├── grades/
│       ├── attendance/
│       ├── announcements/
│       ├── schedule/
│       ├── messages/
│       └── reports/
├── frontend/
│   ├── css/
│   ├── js/
│   └── images/
├── requirements.txt
├── .env.example
└── README.md
```

### 1.4 Dependencies Installation
```bash
# requirements.txt
Django>=5.0
psycopg2-binary>=2.9
python-dotenv>=1.0
Pillow>=10.0
django-cors-headers>=4.0
```

### 1.5 Git Setup
- Initialize git repository
- Create .gitignore
- Initial commit

## Deliverables
- [x] Django project created
- [x] PostgreSQL configured
- [x] Project structure established
- [x] Dependencies installed
- [x] Git repository initialized

## Next Phase
[Phase 2: Authentication & Users](./02-phase-authentication.md)
