from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def role_required(*allowed_roles):
    """Restrict a view to the given roles.

    Anonymous visitors go to the login page; a signed-in user with the wrong
    role is sent back to their own dashboard with an explanation rather than
    being bounced to a login form they are already past.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request)
            if request.user.role not in allowed_roles:
                messages.error(request, 'You do not have access to that page.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def redirect_to_login(request):
    from django.contrib.auth.views import redirect_to_login as _redirect

    return _redirect(request.get_full_path())


admin_required = role_required('admin')
teacher_required = role_required('teacher')
student_required = role_required('student')
parent_required = role_required('parent')
staff_required = role_required('admin', 'teacher')
