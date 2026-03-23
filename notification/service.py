# services/notification_service.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification


def push_notification(sender, receiver, type, content="", url="", obj=None):
    # 1. Lưu DB
    noti = Notification.objects.create(
        sender=sender,
        receiver=receiver,
        type=type,
        content=content,
        url=url,
        object_id=getattr(obj, "id", None),
        object_type=obj.__class__.__name__ if obj else None
    )

    # 2. Push realtime
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"noti_{receiver.id}",
        {
            "type": "send_notification",
            "data": {
                "id": noti.id,
                "sender": sender.username,
                "avatar_sender": sender.avatar.url if sender.avatar else None,
                # Client expects data.type == "notification"
                "type": "notification",
                "event_type": type,
                "content": content,
                "url": url,
                "created_at": str(noti.created_at),
            }
        }
    )
    
