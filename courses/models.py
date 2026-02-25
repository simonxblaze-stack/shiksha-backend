import uuid
from django.db import models
from django.conf import settings


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="subjects",
    )

    name = models.CharField(max_length=100)

    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="teaching_subjects",
        blank=True,
    )

    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("course", "name")

    def __str__(self):
        return f"{self.course.title} → {self.name}"


class Chapter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="chapters",
    )

    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("subject", "title")

    def __str__(self):
        return self.title


class CourseDetail(models.Model):
    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        related_name="details"
    )

    level = models.CharField(max_length=50)
    duration_weeks = models.PositiveIntegerField()
    syllabus = models.TextField(blank=True)

    language = models.CharField(max_length=50, default="English")
    requirements = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Details of {self.course.title}"
