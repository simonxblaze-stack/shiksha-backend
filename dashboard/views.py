from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from enrollments.models import Enrollment
from courses.models import Subject, Chapter

from livestream.models import LiveSession
from assignments.models import Assignment
from quizzes.models import Quiz
from activity.models import Activity

from .serializers import (
    DashboardSessionSerializer,
    DashboardAssignmentSerializer,
    DashboardQuizSerializer,
    DashboardActivitySerializer
)


class DashboardView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        # enrolled courses
        course_ids = Enrollment.objects.filter(
            user=user,
            status=Enrollment.STATUS_ACTIVE
        ).values_list("course_id", flat=True)

        # subjects
        subject_ids = Subject.objects.filter(
            course_id__in=course_ids
        ).values_list("id", flat=True)

        # chapters
        chapter_ids = Chapter.objects.filter(
            subject_id__in=subject_ids
        ).values_list("id", flat=True)

        # live sessions
        sessions = (
            LiveSession.objects
            .filter(
                subject_id__in=subject_ids,
                start_time__gte=timezone.now()
            )
            .select_related("subject", "created_by")
            .order_by("start_time")[:6]
        )

        # assignments
        assignments = (
            Assignment.objects
            .filter(chapter_id__in=chapter_ids)
            .select_related("chapter__subject")
            .order_by("due_date")[:5]
        )

        # quizzes
        quizzes = (
            Quiz.objects
            .filter(
                subject_id__in=subject_ids,
                is_published=True
            )
            .select_related("created_by")
            .order_by("due_date")[:5]
        )

        # notifications from activity
        notifications = (
            Activity.objects
            .filter(user=user)
            .order_by("-created_at")[:10]
        )

        # schedule items
        schedule = (
            Activity.objects
            .filter(user=user)
            .order_by("due_date")[:10]
        )

        return Response({

            "sessions": DashboardSessionSerializer(
                sessions, many=True
            ).data,

            "assignments": DashboardAssignmentSerializer(
                assignments, many=True
            ).data,

            "quizzes": DashboardQuizSerializer(
                quizzes, many=True
            ).data,

            "notifications": DashboardActivitySerializer(
                notifications, many=True
            ).data,

            "schedule": DashboardActivitySerializer(
                schedule, many=True
            ).data
        })
