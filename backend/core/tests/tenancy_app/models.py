from django.db import models

from core.models import TenantModel


class Course(TenantModel):
    title = models.CharField(max_length=100)


class Lesson(TenantModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=100)
