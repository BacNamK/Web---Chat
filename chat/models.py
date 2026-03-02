from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["room", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.room}"