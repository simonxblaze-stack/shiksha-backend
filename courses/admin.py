from django.contrib import admin
from .models import Course, Subject, Chapter


# =========================
# COURSE ADMIN
# =========================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    search_fields = ("title",)
    list_filter = ("created_at",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "order", "get_teachers")
    list_filter = ("course",)
    ordering = ("course", "order")
    search_fields = ("name", "course__title")
    filter_horizontal = ("teachers",)

    def get_teachers(self, obj):
        return ", ".join([t.email for t in obj.teachers.all()])

    get_teachers.short_description = "Teachers"


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "order")
    list_filter = ("subject",)
    ordering = ("subject", "order")
