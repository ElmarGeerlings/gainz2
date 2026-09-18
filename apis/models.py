from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ApiCall(models.Model):
    provider = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=16)
    url = models.TextField()
    request = models.JSONField(null=True, blank=True)
    response_code = models.IntegerField(null=True, blank=True)
    response = models.JSONField(null=True, blank=True)
    exception = models.TextField(blank=True)
    extra = models.JSONField(default=dict, blank=True)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.provider} {self.method} {self.response_code} @ {self.created_at}"
