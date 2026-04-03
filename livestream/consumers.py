from channels.generic.websocket import AsyncWebsocketConsumer
import json


class LiveSessionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.group_name = f"session_{self.session_id}"

        # join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def session_update(self, event):
        # send update to frontend
        await self.send(text_data=json.dumps(event["data"]))
