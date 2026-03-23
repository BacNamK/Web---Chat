import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model


class PresenceConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add("presence", self.channel_name)

        self.received_pong = True

        await self.accept()
        await self.get_user_status(self.user.id,True)

        self.heartbeat_task = asyncio.create_task(self.send_heartbeat())

        # broadcast online
        await self.channel_layer.group_send(
            "presence",
            {
                "type": "user_status",
                "user_id": self.user.id,
                "status": True
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, "heartbeat_task"):
            self.heartbeat_task.cancel()    

        await self.get_user_status(self.user.id,False)

        await self.channel_layer.group_send(
            "presence",
            {
                "type": "user_status",
                "user_id": self.user.id,
                "status": False
            }
        )

        await self.channel_layer.group_discard("presence", self.channel_name)

    async def user_status(self, event):
        await self.send(text_data=json.dumps(event))

    async def send_heartbeat(self):
        try:
            while True:
                self.received_pong = False

                await self.send(text_data=json.dumps({"type": "ping"}))
                await asyncio.sleep(30)

                if not self.received_pong:
                    await self.close()
                    break
                
                await asyncio.sleep(270)
            
        except asyncio.CancelledError:
            pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("type") == "pong":
            self.received_pong = True

    @database_sync_to_async
    def get_user_status(self, user_id,status):

        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            user.status = status
            user.last_seen = timezone.now()
            user.save(update_fields=["status", "last_seen"])
            return user.id
        except User.DoesNotExist:
            return False