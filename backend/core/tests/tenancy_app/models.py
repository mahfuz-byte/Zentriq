from django.db import models

from core.models import TenantModel


class Course(TenantModel):
    title = models.CharField(max_length=100)
    prerequisite = models.ForeignKey("self", null=True, on_delete=models.SET_NULL)
    tags = models.ManyToManyField("Tag", through="CourseTag", related_name="courses")


class Lesson(TenantModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=100)


class Syllabus(TenantModel):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name="syllabus")


class Tag(TenantModel):
    name = models.CharField(max_length=50)


class CourseTag(TenantModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
