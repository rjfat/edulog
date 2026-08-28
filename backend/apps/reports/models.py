from django.db import models

from apps.accounts.models import User


class AuditLog(models.Model):
    """A read-only trail of who did what, when, and from where."""

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=100)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        actor = self.user.display_name if self.user_id else 'System'
        return f'{self.action} by {actor}'

    @classmethod
    def recent(cls, limit=10):
        return cls.objects.select_related('user').order_by('-created_at')[:limit]


class SchoolSettings(models.Model):
    """Single-row site configuration; `load()` hands back the one true row."""

    school_name = models.CharField(max_length=200, default='EduLog')
    academic_year = models.CharField(max_length=20, blank=True)
    term_label = models.CharField(max_length=50, blank=True)
    contact_email = models.EmailField(blank=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='settings_updates',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'school settings'

    def __str__(self):
        return f'Settings for {self.school_name}'

    @classmethod
    def load(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings