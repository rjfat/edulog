"""Audit helpers.

The middleware stashes the current request in a thread-local so signal
receivers can attribute an action to a user and an IP without the callers
threading a request object through model saves.
"""

import threading

from .models import AuditLog

_thread_locals = threading.local()


class AuditLogMiddleware:
    """Capture the request for the duration of its response cycle."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        try:
            return self.get_response(request)
        finally:
            _thread_locals.request = None


def current_request():
    return getattr(_thread_locals, 'request', None)


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_action(action, details='', actor=None, request=None):
    """Write one audit entry.

    The actor falls back to the signed-in user on the current request; the IP
    is read from the request when one is available.
    """
    request = request or current_request()
    ip = None
    if request is not None:
        ip = client_ip(request)
        if actor is None and getattr(request, 'user', None) is not None:
            if request.user.is_authenticated:
                actor = request.user
    AuditLog.objects.create(user=actor, action=action, details=details, ip_address=ip)