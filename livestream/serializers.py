from rest_framework import serializers
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import uuid

from .models import LiveSession
from courses.models import Subject


# =========================
# CREATE SERIALIZER
# =========================
class LiveSessionCreateSerializer(serializers.ModelSerializer):
    subject_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = LiveSession
        fields = [
            "id",
            "title",
            "description",
            "start_time",
            "end_time",
            "subject_id",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        request = self.context.get("request")
        user = request.user

        # =========================
        # ROLE CHECK
        # =========================
        if not user.has_role("TEACHER"):
            raise serializers.ValidationError(
                {"non_field_errors": ["Only teachers can schedule sessions."]}
            )

        # =========================
        # SUBJECT VALIDATION
        # =========================
        try:
            subject = Subject.objects.select_related("course").get(
                id=data["subject_id"]
            )
        except Subject.DoesNotExist:
            raise serializers.ValidationError(
                {"subject_id": ["Invalid subject."]}
            )

        if not subject.subject_teachers.filter(teacher=user).exists():
            raise serializers.ValidationError(
                {"non_field_errors": ["You are not assigned to this subject."]}
            )

        start_time = data["start_time"]
        end_time = data["end_time"]

        # =========================
        # TIMEZONE FIX (SAFE)
        # =========================
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)

        if timezone.is_naive(end_time):
            end_time = timezone.make_aware(end_time)

        data["start_time"] = start_time
        data["end_time"] = end_time

        now = timezone.now()

        # =========================
        # BASIC VALIDATION
        # =========================
        if start_time >= end_time:
            raise serializers.ValidationError(
                {"end_time": ["End time must be after start time."]}
            )

        if start_time <= now:
            raise serializers.ValidationError(
                {"start_time": ["Cannot schedule a session in the past."]}
            )

        # =========================
        # OVERLAP CHECK (CRITICAL)
        # =========================
        conflict = (
            LiveSession.objects
            .filter(
                subject=subject,
                created_by=user,
            )
            .exclude(
                status__in=[
                    LiveSession.STATUS_CANCELLED,
                    LiveSession.STATUS_COMPLETED,
                ]
            )
            .filter(
                Q(start_time__lt=end_time) &
                Q(end_time__gt=start_time)
            )
            .order_by("start_time")
            .first()
        )

        if conflict:
            start_str = timezone.localtime(
                conflict.start_time).strftime('%d %b %H:%M')
            end_str = timezone.localtime(conflict.end_time).strftime('%H:%M')

            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        f"Conflicts with another session: {conflict.title} ({start_str} - {end_str})"
                    ]
                }
            )

        self._validated_subject = subject
        return data

    def create(self, validated_data):
        subject = self._validated_subject
        user = self.context["request"].user

        validated_data.pop("subject_id", None)

        room_name = f"session_{uuid.uuid4().hex}"

        return LiveSession.objects.create(
            subject=subject,
            course=subject.course,
            room_name=room_name,
            created_by=user,
            **validated_data
        )


# =========================
# LIST SERIALIZER
# =========================
class LiveSessionListSerializer(serializers.ModelSerializer):
    teacher = serializers.CharField(source="created_by.email", read_only=True)
    can_join = serializers.SerializerMethodField()
    computed_status = serializers.SerializerMethodField()

    subject_id = serializers.UUIDField(source="subject.id", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    course_name = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = LiveSession
        fields = [
            "id",
            "title",
            "start_time",
            "end_time",
            "computed_status",
            "teacher",
            "can_join",
            "subject_id",
            "subject_name",
            "course_name",
        ]

    # =========================
    # 🔥 SINGLE SOURCE OF TRUTH
    # =========================
    def get_computed_status(self, obj):
        return obj.computed_status()

    # =========================
    # JOIN LOGIC (ALIGNED)
    # =========================
    def get_can_join(self, obj):
        request = self.context.get("request")
        now = timezone.now()

        status = obj.computed_status()

        # 🚫 hard blocks
        if status in [
            LiveSession.STATUS_CANCELLED,
            LiveSession.STATUS_COMPLETED,
        ]:
            return False

        # 👨‍🏫 teacher always allowed
        if request and request.user.has_role("TEACHER"):
            return True

        # 👨‍🎓 student join window
        return now >= obj.start_time - timedelta(minutes=15)
