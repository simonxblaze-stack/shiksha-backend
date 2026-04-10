# isort: skip_file
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from django.utils import timezone

from livestream.services.session_state import get_session_state, set_session_state
from .models import LiveSession


class LiveSessionConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.group_name = f"session_{self.session_id}"
        self.user = self.scope["user"]

        # join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # 🔥 GET STATE FROM REDIS
        state = await database_sync_to_async(get_session_state)(self.session_id)

        # 🔥 FALLBACK TO DB
        if not state:
            try:
                session = await database_sync_to_async(
                    LiveSession.objects.get
                )(id=self.session_id)

                state = {
                    "status": session.computed_status(),
                    "teacher_left_at": (
                        session.teacher_left_at.isoformat()
                        if session.teacher_left_at else None
                    ),
                }

                # save to Redis
                await database_sync_to_async(set_session_state)(session)
            except LiveSession.DoesNotExist:
                state = {"status": "UNKNOWN"}

        # 🔥 SEND INITIAL STATE
        await self.send(text_data=json.dumps({
            "type": "initial_state",
            "data": state
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming messages from WebSocket client."""
        try:
            data = json.loads(text_data)
            msg_type = data.get("type")

            if msg_type == "chat_message":
                await self.handle_chat(data)

        except json.JSONDecodeError:
            pass

    async def handle_chat(self, data):
        """Broadcast chat message to all participants in the session."""
        user = self.scope["user"]

        if user.is_anonymous:
            return

        # Get user info
        sender_name = await self.get_user_name(user)
        role = await self.get_user_role(user)

        message = {
            "type": "chat_message",
            "data": {
                "sender": sender_name,
                "text": data.get("text", ""),
                "role": role,
                "isTeacher": role == "TEACHER",
                "time": timezone.now().isoformat(),
                "sender_id": str(user.id),
            }
        }

        # Broadcast to all in session group
        await self.channel_layer.group_send(
            self.group_name,
            message
        )

    @database_sync_to_async
    def get_user_name(self, user):
        try:
            profile = user.profile
            return profile.full_name or profile.first_name or user.email
        except Exception:
            return user.email

    @database_sync_to_async
    def get_user_role(self, user):
        try:
            from accounts.models import UserRole
            role = UserRole.objects.filter(
                user=user,
                is_primary=True,
                is_active=True
            ).select_related("role").first()
            return role.role.name if role else "STUDENT"
        except Exception:
            return "STUDENT"

    async def session_update(self, event):
        """Receive session status update and forward to client."""
        await self.send(text_data=json.dumps({
            "type": "session_update",
            "data": event["data"]
        }))

    async def chat_message(self, event):
        """Receive chat message from group and forward to client."""
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "data": event["data"]
        }))