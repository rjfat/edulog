"""Turn important data changes into audit entries.

Everything subscribers care about creating or deleting fires a log_action().
Updates to users and settings are logged explicitly in the views that own
them because only those call sites know what actually changed.
"""

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_delete, post_save

from apps.accounts.models import User
from apps.announcements.models import Announcement
from apps.attendance.models import Attendance
from apps.courses.models import Course, Enrollment
from apps.grades.models import Grade
from apps.messaging.models import Message
from apps.schedule.models import Schedule

from .audit import log_action


def _describe(obj):
    text = str(obj)
    return text if len(text) <= 140 else text[:137] + '...'


def _make_logger(action):
    def receive(sender, instance, created=False, **kwargs):
        log_action(action, _describe(instance))
    return receive


def _make_delete_logger(action):
    def receive(sender, instance, **kwargs):
        log_action(action, _describe(instance))
    return receive


def on_login(sender, request, user, **kwargs):
    log_action('auth.login', f'{user.display_name} signed in', actor=user, request=request)


def on_logout(sender, request, user, **kwargs):
    log_action('auth.logout', f'{user.display_name} signed out', actor=user, request=request)


LOG_CREATES = {
    User: 'user.created',
    Course: 'course.created',
    Enrollment: 'enrollment.created',
    Grade: 'grade.created',
    Attendance: 'attendance.marked',
    Announcement: 'announcement.created',
    Message: 'message.sent',
    Schedule: 'schedule.created',
}

LOG_DELETES = {
    User: 'user.deleted',
    Course: 'course.deleted',
    Enrollment: 'enrollment.deleted',
    Grade: 'grade.deleted',
    Attendance: 'attendance.deleted',
    Announcement: 'announcement.deleted',
    Schedule: 'schedule.deleted',
}


def register_audit_signals():
    for model, action in LOG_CREATES.items():
        post_save.connect(_make_logger(action), sender=model, weak=False,
                          dispatch_uid=f'audit.{model._meta.label}.created')
    for model, action in LOG_DELETES.items():
        post_delete.connect(_make_delete_logger(action), sender=model, weak=False,
                            dispatch_uid=f'audit.{model._meta.label}.deleted')
    user_logged_in.connect(on_login, weak=False, dispatch_uid='audit.auth.login')
    user_logged_out.connect(on_logout, weak=False, dispatch_uid='audit.auth.logout')