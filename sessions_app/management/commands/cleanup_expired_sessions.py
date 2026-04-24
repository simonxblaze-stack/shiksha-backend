"""
Safety-net management command to auto-end private sessions that have been
empty (all participants left) for longer than the grace period.

This catches edge cases where Daphne restarted and the in-memory asyncio
timer was lost.

Usage:
    python manage.py cleanup_expired_sessions

Run via cron every few minutes on the server, e.g.:
    */3 * * * * cd /path/to/project && python manage.py cleanup_expired_sessions
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from sessions_app.models import PrivateSession, StudyGroupSession
from sessions_app.views import _end_session_internal


# Must match AUTO_EXPIRE_DELAY in consumers.py
GRACE_PERIOD = timedelta(minutes=5)
# Must match STUDY_GROUP_AUTO_EXPIRE_DELAY in consumers.py
STUDY_GROUP_GRACE_PERIOD = timedelta(minutes=7)


class Command(BaseCommand):
    help = (
        "Auto-end private sessions where all participants left 5+ minutes "
        "ago, and study groups where all participants left 7+ minutes ago. "
        "Also hard-expires study groups whose selected duration has elapsed."
    )

    def handle(self, *args, **options):
        # ── Private sessions (unchanged behaviour) ───────────────────
        cutoff = timezone.now() - GRACE_PERIOD
        orphaned = PrivateSession.objects.filter(
            status="ongoing",
            all_left_at__isnull=False,
            all_left_at__lte=cutoff,
            active_connections__lte=0,
        )
        count = 0
        for session in orphaned:
            ended = _end_session_internal(session, reason="cleanup_command")
            if ended:
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  Auto-ended session {session.id}")
                )
        if count:
            self.stdout.write(
                self.style.SUCCESS(f"Cleaned up {count} expired session(s).")
            )
        else:
            self.stdout.write("No orphaned sessions found.")

        # ── Study groups: idle cleanup ───────────────────────────────
        from sessions_app.study_group_views import _end_study_group_internal

        sg_cutoff = timezone.now() - STUDY_GROUP_GRACE_PERIOD
        sg_orphaned = StudyGroupSession.objects.filter(
            status="live",
            all_left_at__isnull=False,
            all_left_at__lte=sg_cutoff,
            active_connections__lte=0,
        )
        sg_count = 0
        for session in sg_orphaned:
            if _end_study_group_internal(session, reason="cleanup_command_idle"):
                sg_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  Auto-ended study group {session.id}")
                )

        # ── Study groups: hard-duration safety net ───────────────────
        now = timezone.now()
        live = StudyGroupSession.objects.filter(
            status="live", room_started_at__isnull=False,
        )
        sg_hard = 0
        for session in live:
            end_at = session.room_started_at + timedelta(minutes=session.duration_minutes)
            if now >= end_at:
                if _end_study_group_internal(session, reason="cleanup_command_duration"):
                    sg_hard += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Duration-expired study group {session.id}"
                        )
                    )

        total_sg = sg_count + sg_hard
        if total_sg:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Cleaned up {total_sg} study group(s) "
                    f"({sg_count} idle, {sg_hard} duration)."
                )
            )
        else:
            self.stdout.write("No orphaned study groups found.")
