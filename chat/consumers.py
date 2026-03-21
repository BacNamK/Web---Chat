from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import json
import datetime
from .models import Message, Room


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    #===
    # DB lAYER
    #===
    
    @sync_to_async
    def _create_message(self, content, replies):

        room, _ = Room.objects.get_or_create(name=self.room_name)


        user = self.scope["user"]

        if user.is_authenticated:
            msg = Message.objects.create(room=room, user=user, content=content, repies_id=replies)
            return msg.id
        return None

    @sync_to_async
    def _delete_message(self,message_id,user):
        try:
            msg = Message.objects.get(id = message_id)
            if msg.user == user or user.is_superuser or user.is_staff:
                msg.is_deleted = True
                msg.save(update_fields=["is_deleted"])
            return False
        except Message.DoesNotExist:
            return False

    #===
    # RECEIVE ENTRY POINT
    #===
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'send_message':
            await self.handle_send(data)
            return
        
        if action == 'delete_message':
            await self.handle_delete(data)
            return

        return
    #===
    # SEND MESSAGE
    #===

    async def handle_send(self, data):

        message = data.get('message')
        user = self.scope['user']
        replies = data.get('replies')

        if not message:
            return

        message_id = await self._create_message(message,replies)

        user_replies = None

        if replies:
            reply_obj = await sync_to_async(
            lambda: Message.objects.select_related('user').get(id=replies))()
            user_replies = {
                "id": reply_obj.id,
                "message": reply_obj.content,
                "username": reply_obj.user.username if reply_obj.user else "Unknown",
            }

        avatar = None
        if user.is_authenticated and user.avatar:
            avatar = str(user.avatar.url)

        await self.channel_layer.group_send(
            self.room_group_name,{
                "type":"chat_message",
                "message":str(message),
                "message_id":int(message_id),
                "username":str(user.username) if user.is_authenticated else "Guest",
                "avatar": avatar,
                "user_id":int(user.id),
                "replies": user_replies,
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

    async def chat_message(self,event):
        await self.send(text_data=json.dumps({
            "action":"send_message",
            "message":event["message"],
            "message_id":event["message_id"],
            "username":event["username"],
            "avatar":event["avatar"],
            "user_id":event["user_id"],
            "replies": event['replies'],
            "timestamp": event["timestamp"],
        }))

    #===
    # DELETE MESSAGE
    #===
    async def handle_delete(self,data):
        message_id = data.get('message_id')
        user = self.scope['user']

        success = await self._delete_message(message_id,user)

        if not success:
            return
        
        await self.channel_layer.group_send(
            self.room_group_name,{
                "type":"delete_message",
                "message_id":message_id,
            }
        )

    async def delete_message(self, event):
        await self.send(text_data=json.dumps({
            "action": "delete_message",
            "message_id": event["message_id"]
        }))
        