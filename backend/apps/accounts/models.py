from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model.

    Swapping in a custom user model has to happen before the first migration,
    so the empty subclass lands in Phase 1. Phase 2 adds the role, contact and
    profile fields.
    """

    pass
