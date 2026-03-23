from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    NOTI_TYPE_CHOICES = (
        ("like", "Like"),
        ("comment", "Comment"),
        ("message", "Message"),
        ("reply", "Reply"),
        ("system", "System"),
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_notifications"
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_notifications"
    )

    type = models.CharField(
        max_length=20,
        choices=NOTI_TYPE_CHOICES
    )

    # object liên quan (post, comment, message...)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_type = models.CharField(max_length=50, null=True, blank=True)

    # nội dung hiển thị
    content = models.TextField(blank=True)

    # link điều hướng
    url = models.URLField(max_length=255, blank=True)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.type})"