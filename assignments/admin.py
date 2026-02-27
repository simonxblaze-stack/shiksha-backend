from django.contrib import admin
from .models import Assignment, AssignmentSubmission


class AssignmentSubmissionInline(admin.TabularInline):
    model = AssignmentSubmission
    extra = 0
    readonly_fields = ("student", "submitted_file", "submitted_at")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "chapter",
        "due_date",
        "created_at",
    )
    list_filter = (
        "due_date",
        "chapter__subject__course",
    )
    search_fields = (
        "title",
        "chapter__subject__name",
        "chapter__subject__course__title",
    )
    ordering = ("-created_at",)
    inlines = [AssignmentSubmissionInline]


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "assignment",
        "student",
        "submitted_at",
    )
    list_filter = (
        "submitted_at",
        "assignment__chapter__subject__course",
    )
    search_fields = (
        "student__email",
        "assignment__title",
    )
    ordering = ("-submitted_at",)
