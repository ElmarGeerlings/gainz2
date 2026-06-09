from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    smartchange_enabled = models.BooleanField(default=False)
    smartchange_warmup = models.BooleanField(default=True)

    def __str__(self):
        return f"Settings for {self.user}"
