from django.db.utils import OperationalError

from .models import SchoolSettings


def school_settings(request):
    """Expose the school name to every page (brand and footer)."""
    try:
        name = SchoolSettings.load().school_name
    except OperationalError:
        # Tables do not exist yet (e.g. before the first migrate).
        name = 'EduLog'
    return {'school_name': name or 'EduLog'}