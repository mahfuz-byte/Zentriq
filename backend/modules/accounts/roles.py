from django.db import models


class Role(models.TextChoices):
    """A school user's role. Public, so other modules can record and check roles
    without importing accounts.models.
    """

    SCHOOL_ADMIN = "SCHOOL_ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"
