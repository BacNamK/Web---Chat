from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Report(models.Model):

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports_sent")
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="reports_received")


    target_id = models.CharField(max_length=255, null=True, blank=True)
    # id của post/comment nếu có (flexible, không FK cứng)

    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return {self.reporter}