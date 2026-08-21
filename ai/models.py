from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from apis.models import ApiCall


class AiChat(models.Model):
    session_id = models.UUIDField(unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    intake = models.JSONField(default=dict)
    messages = models.JSONField(default=list)
    drafts = models.JSONField(default=list)
    api_calls = GenericRelation(ApiCall)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"AiChat {self.session_id} ({self.user_id})"
