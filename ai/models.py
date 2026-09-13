from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from apis.models import ApiCall


class AiChat(models.Model):
    session_id = models.UUIDField(unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    guest_id = models.UUIDField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    intake = models.JSONField(default=dict)
    messages = models.JSONField(default=list)
    drafts = models.JSONField(default=list)
    api_calls = GenericRelation(ApiCall)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["guest_id", "created_at"]),
        ]

    def __str__(self):
        if self.user_id:
            return f"AiChat {self.session_id} ({self.user_id})"
        return f"AiChat {self.session_id} (guest {self.guest_id})"

    @property
    def owner_label(self):
        if self.user_id:
            return self.user.username
        return str(self.guest_id)
