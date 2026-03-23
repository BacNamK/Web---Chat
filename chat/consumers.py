import json
import datetime
import redis.asyncio as redis

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from .models import Message, Room

User = get_user_model()

r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

SOCKET_TTL = 30  # seconds — must be > heartbeat interval


class ChatConsumer(AsyncWebsocketConsumer):

    # =====================
    # CONNECT
    # =====================
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]

        # Khởi tạo sớm để disconnect() luôn có key dù connect() lỗi giữa chừng
        self.socket_key = None
        self.room_key = None

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        if not self.user.is_authenticated:
            await self.accept()
            return

        self.socket_key = f"room:{self.room_name}:user:{self.user.id}:sockets"
        self.room_key = f"room:{self.room_name}:users"

        # Thêm socket + TTL
        await r.sadd(self.socket_key, self.channel_name)
        await r.expire(self.socket_key, SOCKET_TTL)

        # Thêm user vào danh sách online
        await r.sadd(self.room_key, self.user.id)

        await self.accept()

        # ===== GỬI DANH SÁCH USER HIỆN TẠI CHO CLIENT MỚI =====
        user_ids = await r.smembers(self.room_key)

        users_data = await sync_to_async(list)(
            User.objects.filter(id__in=user_ids)
            .values("id", "username", "avatar","is_staff","is_superuser")
        )

        await self.send(text_data=json.dumps({
            "type": "init_users",
            "users": [
                {
                    "user_id": u["id"],
                    "id": u["id"],
                    "username": u["username"],
                    "avatar": u["avatar"],
                    "is_staff": u["is_staff"],
                    "is_superuser": u["is_superuser"],
                }
                for u in users_data
            ],
        }))

        # ===== BROADCAST JOIN CHO CÁC CLIENT KHÁC =====
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "user_id": self.user.id,
                "type": "user_join",
                "username": self.user.username,
                "avatar": str(self.user.avatar.url) if self.user.avatar else None,
                "sender_channel": self.channel_name,   # dùng để lọc, không gửi xuống client
            }
        )

    # =====================
    # DISCONNECT
    # =====================
    async def disconnect(self, close_code):
        # Luôn rời group để tránh leak channel
        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except Exception:
            pass

        # Nếu chưa authen hoặc connect() lỗi trước khi set key thì dừng
        if not self.user.is_authenticated or not self.socket_key:
            return

        try:
            # Xóa socket này khỏi set
            await r.srem(self.socket_key, self.channel_name)

            # Kiểm tra còn socket nào không
            remaining = await r.scard(self.socket_key)

            if remaining == 0:
                # Dọn sạch key socket
                await r.delete(self.socket_key)

                # Xóa user khỏi danh sách online
                await r.srem(self.room_key, self.user.id)

                # Broadcast user offline
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "user_leave",
                        "user_id": self.user.id,
                    }
                )
        except Exception as e:
            print(f"[disconnect] Redis error for user {self.user.id}: {e}")

    # =====================
    # PRESENCE EVENTS
    # =====================
    async def user_join(self, event):
        # Không gửi lại cho chính channel vừa join
        if event.get("sender_channel") == self.channel_name:
            return

        await self.send(text_data=json.dumps({
            "type": "user_join",
            "user_id": event["user_id"],
            "username": event["username"],
            "avatar": event["avatar"],
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_leave",
            "user_id": event["user_id"],
        }))

    # =====================
    # RECEIVE (heartbeat + actions)
    # =====================
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            print(f"[receive] Invalid JSON: {e}")
            return

        try:
            # ===== HEARTBEAT =====
            if data.get("type") == "ping":
                await self._handle_ping()
                return

            action = data.get("action")

            if action == "send_message":
                await self.handle_send(data)

            elif action == "delete_message":
                await self.handle_delete(data)

        except Exception as e:
            print(f"[receive] Error handling action '{data.get('action')}': {e}")

    async def _handle_ping(self):
        """Refresh TTL khi nhận heartbeat từ client."""
        if self.socket_key:
            try:
                await r.expire(self.socket_key, SOCKET_TTL)
            except Exception as e:
                print(f"[ping] Redis error: {e}")

    # =====================
    # SEND MESSAGE
    # =====================
    async def handle_send(self, data):
        message = data.get("message", "").strip()
        replies = data.get("replies")
        user_reply = data.get("user_reply")
        message_reply = data.get("message_reply")
        user_reply_id = data.get("user_reply_id")
        avatar_reply = data.get("avatar_reply")

        if not message:
            return

        message_id = await self._create_message(message, replies)

        if message_id is None:
            return

        avatar = None
        if self.user.is_authenticated and self.user.avatar:
            avatar = str(self.user.avatar.url)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "user_reply": user_reply,
                "message_reply": message_reply,
                "avatar_reply": avatar_reply,
                "message_id": int(message_id),
                "username": self.user.username if self.user.is_authenticated else "Guest",
                "avatar": avatar,
                "user_id": self.user.id if self.user.is_authenticated else None,
                "is_staff": self.user.is_staff if self.user.is_authenticated else False,
                "is_superuser": self.user.is_superuser if self.user.is_authenticated else False,
                "timestamp": datetime.datetime.now().isoformat(),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "action": "send_message",
            "message": event["message"],
            "user_reply": event["user_reply"],
            "message_reply": event["message_reply"],
            "avatar_reply": event["avatar_reply"],
            "message_id": event["message_id"],
            "username": event["username"],
            "avatar": event["avatar"],
            "user_id": event["user_id"],
            "is_staff": event["is_staff"],
            "is_superuser": event["is_superuser"],
            "timestamp": event["timestamp"],
        }))

    # =====================
    # DELETE MESSAGE
    # =====================
    async def handle_delete(self, data):
        message_id = data.get("message_id")

        if not message_id:
            return

        success = await self._delete_message(message_id, self.user)

        if not success:
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "delete_message",
                "message_id": message_id,
            }
        )

    async def delete_message(self, event):
        await self.send(text_data=json.dumps({
            "action": "delete_message",
            "message_id": event["message_id"],
        }))

    # =====================
    # DB LAYER
    # =====================
    @sync_to_async
    def _create_message(self, content, replies):
        if not self.user.is_authenticated:
            return None

        room, _ = Room.objects.get_or_create(name=self.room_name)

        msg = Message.objects.create(
            room=room,
            user=self.user,
            content=content,
            repies_id=replies,
        )
        return msg.id

    @sync_to_async
    def _delete_message(self, message_id, user):
        try:
            msg = Message.objects.get(id=message_id)

            if msg.user == user or user.is_staff or user.is_superuser:
                msg.is_deleted = True
                msg.save(update_fields=["is_deleted"])
                return True

            return False
        except Message.DoesNotExist:
            return False